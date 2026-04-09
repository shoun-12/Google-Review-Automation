from __future__ import annotations

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlencode
from uuid import UUID
from uuid import uuid4

import httpx
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.core.security import create_refresh_token
from app.core.security import decode_token
from app.core.security import verify_password
from app.models.entities import LoginOAuthState
from app.models.entities import Membership
from app.models.entities import RefreshToken
from app.models.entities import User
from app.schemas.auth import AuthResponse
from app.schemas.auth import GoogleLoginStartResponse
from app.schemas.auth import MeResponse
from app.schemas.auth import MembershipSummary
from app.schemas.auth import RefreshTokenResponse
from app.schemas.auth import UserSummary

GOOGLE_LOGIN_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_LOGIN_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_LOGIN_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_LOGIN_STATE_TTL_MINUTES = 10


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return user


def build_membership_summaries(db: Session, user_id: UUID) -> list[MembershipSummary]:
    memberships = db.scalars(select(Membership).where(Membership.user_id == user_id)).all()
    return [MembershipSummary.model_validate(item) for item in memberships]


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(str(user.id))
    refresh_token, token_jti, expires_at = create_refresh_token(str(user.id))
    db.add(
        RefreshToken(
            user_id=user.id,
            token_jti=token_jti,
            expires_at=expires_at,
        )
    )
    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)
    return access_token, refresh_token


def build_auth_response(db: Session, user: User) -> AuthResponse:
    access_token, refresh_token = issue_tokens(db, user)
    memberships = build_membership_summaries(db, user.id)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserSummary.model_validate(user),
        memberships=memberships,
    )


def login(db: Session, email: str, password: str) -> AuthResponse:
    user = authenticate_user(db, email, password)
    return build_auth_response(db, user)


def refresh(db: Session, token: str) -> RefreshTokenResponse:
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        user_id = UUID(payload["sub"])
        token_jti = payload["jti"]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_jti == token_jti))
    if stored_token is None or stored_token.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked",
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active",
        )

    stored_token.revoked_at = datetime.now(UTC)
    access_token, refresh_token = issue_tokens(db, user)
    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def logout(db: Session, token: str) -> None:
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        token_jti = payload["jti"]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    stored_token = db.scalar(select(RefreshToken).where(RefreshToken.token_jti == token_jti))
    if stored_token is None:
        return

    stored_token.revoked_at = datetime.now(UTC)
    db.commit()


def me(db: Session, user: User) -> MeResponse:
    memberships = build_membership_summaries(db, user.id)
    return MeResponse(
        user=UserSummary.model_validate(user),
        memberships=memberships,
        last_login_at=user.last_login_at,
    )


def ensure_google_login_configured() -> None:
    required = [
        settings.google_login_client_id,
        settings.google_login_client_secret,
        settings.google_login_redirect_uri,
        settings.web_base_url,
    ]
    if any(not value for value in required):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google login is not configured",
        )


def build_google_login_authorization_url(state_token: str) -> str:
    params = {
        "client_id": settings.google_login_client_id,
        "redirect_uri": settings.google_login_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.google_login_scopes),
        "state": state_token,
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "select_account consent",
    }
    return f"{GOOGLE_LOGIN_AUTH_URL}?{urlencode(params)}"


def start_google_login(db: Session) -> GoogleLoginStartResponse:
    ensure_google_login_configured()
    state_token = uuid4().hex
    db.add(
        LoginOAuthState(
            state_token=state_token,
            expires_at=datetime.now(UTC) + timedelta(minutes=GOOGLE_LOGIN_STATE_TTL_MINUTES),
            redirect_path="/login",
        )
    )
    db.commit()
    return GoogleLoginStartResponse(
        authorization_url=build_google_login_authorization_url(state_token),
    )


def _pop_google_login_state(db: Session, state_token: str) -> LoginOAuthState:
    state = db.scalar(select(LoginOAuthState).where(LoginOAuthState.state_token == state_token))
    if state is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login session is invalid or has expired",
        )

    if state.expires_at < datetime.now(UTC):
        db.delete(state)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login session has expired",
        )

    db.delete(state)
    db.commit()
    return state


async def exchange_google_login_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GOOGLE_LOGIN_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_login_client_id,
                "client_secret": settings.google_login_client_secret,
                "redirect_uri": settings.google_login_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google login token exchange failed",
        )
    return response.json()


async def fetch_google_login_userinfo(access_token: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            GOOGLE_LOGIN_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if not response.is_success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read Google account details",
        )
    return response.json()


def get_google_login_user(db: Session, email: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This Google account is not registered for dashboard access",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive",
        )

    active_membership = db.scalar(
        select(Membership).where(Membership.user_id == user.id, Membership.is_active.is_(True))
    )
    if active_membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user does not belong to an active tenant",
        )

    return user


def _build_frontend_login_redirect(params: dict[str, str]) -> str:
    return f"{settings.web_base_url.rstrip('/')}/login?{urlencode(params)}"


def build_google_login_error_redirect(message: str) -> str:
    return _build_frontend_login_redirect(
        {
            "google_login": "error",
            "message": message,
        }
    )


def build_google_login_success_redirect(auth_response: AuthResponse) -> str:
    return _build_frontend_login_redirect(
        {
            "google_login": "success",
            "access_token": auth_response.access_token,
            "refresh_token": auth_response.refresh_token,
        }
    )


async def complete_google_login(db: Session, code: str | None, state: str | None, error: str | None) -> str:
    try:
        ensure_google_login_configured()
        if error:
            return build_google_login_error_redirect("Google sign-in was canceled or denied")
        if not code or not state:
            return build_google_login_error_redirect("Google sign-in response is incomplete")

        _pop_google_login_state(db, state)
        token_payload = await exchange_google_login_code_for_tokens(code)
        userinfo = await fetch_google_login_userinfo(token_payload["access_token"])
        if not userinfo.get("email") or not userinfo.get("email_verified"):
            return build_google_login_error_redirect("Google account email could not be verified")

        user = get_google_login_user(db, str(userinfo["email"]).strip().lower())
        auth_response = build_auth_response(db, user)
        return build_google_login_success_redirect(auth_response)
    except HTTPException as exc:
        return build_google_login_error_redirect(str(exc.detail))
    except Exception:
        return build_google_login_error_redirect("Google sign-in failed unexpectedly")

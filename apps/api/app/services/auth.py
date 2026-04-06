from __future__ import annotations

from datetime import UTC
from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.core.security import create_refresh_token
from app.core.security import decode_token
from app.core.security import verify_password
from app.models.entities import Membership
from app.models.entities import RefreshToken
from app.models.entities import User
from app.schemas.auth import AuthResponse
from app.schemas.auth import MeResponse
from app.schemas.auth import MembershipSummary
from app.schemas.auth import RefreshTokenResponse
from app.schemas.auth import UserSummary


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


def login(db: Session, email: str, password: str) -> AuthResponse:
    user = authenticate_user(db, email, password)
    access_token, refresh_token = issue_tokens(db, user)
    memberships = build_membership_summaries(db, user.id)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=UserSummary.model_validate(user),
        memberships=memberships,
    )


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

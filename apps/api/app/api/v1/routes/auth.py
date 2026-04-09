from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User
from app.schemas.auth import AuthResponse
from app.schemas.auth import GoogleLoginStartResponse
from app.schemas.auth import LoginRequest
from app.schemas.auth import LogoutRequest
from app.schemas.auth import MeResponse
from app.schemas.auth import RefreshTokenRequest
from app.schemas.auth import RefreshTokenResponse
from app.services.auth import complete_google_login
from app.services.auth import login as login_user
from app.services.auth import logout as logout_user
from app.services.auth import me as me_service
from app.services.auth import refresh as refresh_tokens
from app.services.auth import start_google_login as start_google_login_service

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return login_user(db, payload.email, payload.password)


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> RefreshTokenResponse:
    return refresh_tokens(db, payload.refresh_token)


@router.post("/google/start", response_model=GoogleLoginStartResponse)
def start_google_login(db: Session = Depends(get_db)) -> GoogleLoginStartResponse:
    return start_google_login_service(db)


@router.get("/google/callback")
async def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    redirect_url = await complete_google_login(db, code, state, error)
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/logout", status_code=204)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    logout_user(db, payload.refresh_token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeResponse:
    return me_service(db, current_user)

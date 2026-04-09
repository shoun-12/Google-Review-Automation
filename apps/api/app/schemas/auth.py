from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginStartResponse(BaseModel):
    authorization_url: str


class UserSummary(BaseModel):
    id: UUID
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class MembershipSummary(BaseModel):
    tenant_id: UUID
    role: str
    email_alerts_enabled: bool
    whatsapp_alerts_enabled: bool
    is_active: bool

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary
    memberships: list[MembershipSummary]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    user: UserSummary
    memberships: list[MembershipSummary]
    last_login_at: datetime | None

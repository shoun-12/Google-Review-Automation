from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserListItem(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone_number: str | None
    is_active: bool
    role: str
    email_alerts_enabled: bool
    whatsapp_alerts_enabled: bool
    last_login_at: datetime | None
    joined_at: datetime


class UserListResponse(BaseModel):
    items: list[UserListItem]


class UserCreateRequest(BaseModel):
    email: str
    full_name: str
    phone_number: str | None = None
    role: str
    password: str
    email_alerts_enabled: bool = True
    whatsapp_alerts_enabled: bool = False


class UserUpdateRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    phone_number: str | None = None
    role: str | None = None
    email_alerts_enabled: bool | None = None
    whatsapp_alerts_enabled: bool | None = None
    is_active: bool | None = None

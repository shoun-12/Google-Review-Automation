from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProfileListItem(BaseModel):
    id: UUID
    business_name: str
    city: str | None
    state: str | None
    brand: str
    avg_rating_cached: float
    total_reviews_cached: int
    auto_respond_enabled: bool
    is_active: bool
    last_review_activity_at: datetime | None
    primary_local_admin_user_id: UUID | None = None
    primary_local_admin_name: str | None = None


class ProfileListResponse(BaseModel):
    items: list[ProfileListItem]


class ProfileUpdateRequest(BaseModel):
    primary_local_admin_user_id: UUID | None = None
    auto_respond_enabled: bool | None = None
    is_active: bool | None = None

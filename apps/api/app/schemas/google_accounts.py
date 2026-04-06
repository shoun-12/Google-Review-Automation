from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class GoogleAccountListItem(BaseModel):
    id: UUID
    email: str
    google_account_id: str | None
    is_active: bool
    token_last_refreshed_at: datetime | None
    scopes_json: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class GoogleAccountListResponse(BaseModel):
    items: list[GoogleAccountListItem]

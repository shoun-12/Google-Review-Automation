from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AuditLogListItem(BaseModel):
    id: UUID
    action: str
    target_type: str
    target_id: str | None
    actor_user_id: UUID | None
    created_at: datetime
    metadata_json: dict

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogListItem]

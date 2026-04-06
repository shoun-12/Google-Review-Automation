from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TenantSummary(BaseModel):
    id: UUID
    name: str
    slug: str

    model_config = {"from_attributes": True}


class ApiMessage(BaseModel):
    message: str


class EntityTimestamps(BaseModel):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

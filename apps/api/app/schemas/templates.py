from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class ReplyTemplateListItem(BaseModel):
    id: UUID
    brand: str
    sentiment: str
    template_text: str
    is_active: bool


class ReplyTemplateListResponse(BaseModel):
    items: list[ReplyTemplateListItem]


class ReplyTemplateUpsertRequest(BaseModel):
    brand: str
    sentiment: str
    template_text: str
    is_active: bool = True

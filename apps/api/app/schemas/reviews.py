from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ReviewListItem(BaseModel):
    id: UUID
    gbp_review_id: str
    business_name: str
    reviewer_name: str | None
    star_rating: int
    review_text: str | None
    sentiment: str
    status: str
    review_posted_at: datetime
    reply_text: str | None = None


class ReviewListResponse(BaseModel):
    items: list[ReviewListItem]


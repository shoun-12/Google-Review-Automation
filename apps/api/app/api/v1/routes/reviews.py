from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.reviews import ReviewListResponse
from app.services.dashboard import list_review_feed


router = APIRouter()


@router.get("", response_model=ReviewListResponse)
def get_reviews(
    sentiment: Literal["positive", "negative"] | None = Query(default=None),
    profile_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=5, ge=1, le=50),
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    return list_review_feed(
        db,
        membership.tenant_id,
        user_id=membership.user_id,
        role=membership.role,
        sentiment=sentiment,
        profile_id=profile_id,
        page=page,
        page_size=page_size,
    )

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.reviews import ReviewListResponse
from app.services.dashboard import list_reviews


router = APIRouter()


@router.get("", response_model=ReviewListResponse)
def get_reviews(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ReviewListResponse:
    return ReviewListResponse(
        items=list_reviews(
            db,
            membership.tenant_id,
            user_id=membership.user_id,
            role=membership.role,
        )
    )

from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard_payload


router = APIRouter()


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    return get_dashboard_payload(
        db,
        membership.tenant_id,
        user_id=membership.user_id,
        role=membership.role,
    )

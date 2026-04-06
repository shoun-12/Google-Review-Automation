from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership
from app.api.deps import require_master_admin
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.reports import ReportOverviewResponse
from app.schemas.reports import SummaryReportResponse
from app.services.reports import build_profiles_csv
from app.services.reports import get_report_overview
from app.services.dashboard import get_summary

router = APIRouter()


@router.get("/summary", response_model=SummaryReportResponse)
def report_summary(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> SummaryReportResponse:
    return get_summary(db, membership.tenant_id)


@router.get("/overview", response_model=ReportOverviewResponse)
def report_overview(
    days: int = Query(default=30, ge=1, le=90),
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ReportOverviewResponse:
    return get_report_overview(
        db,
        membership.tenant_id,
        days,
        user_id=membership.user_id,
        role=membership.role,
    )


@router.get("/profiles.csv")
def export_profiles_csv(
    days: int = Query(default=30, ge=1, le=90),
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> Response:
    csv_content = build_profiles_csv(db, membership.tenant_id, days)
    headers = {
        "Content-Disposition": f'attachment; filename="profile-performance-{days}d.csv"',
    }
    return Response(content=csv_content, media_type="text/csv", headers=headers)

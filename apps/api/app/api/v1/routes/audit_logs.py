from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import require_master_admin
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.audit_logs import AuditLogListResponse
from app.services.audit_logs import list_audit_logs


router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
def get_audit_logs(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    return AuditLogListResponse(items=list_audit_logs(db, membership.tenant_id))

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AuditLog
from app.schemas.audit_logs import AuditLogListItem


def list_audit_logs(db: Session, tenant_id, limit: int = 100) -> list[AuditLogListItem]:
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [AuditLogListItem.model_validate(row) for row in rows]

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import AuditLog


def write_audit_log(
    db: Session,
    *,
    tenant_id,
    action: str,
    target_type: str,
    target_id: str | None = None,
    actor_user_id=None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.flush()
    return entry

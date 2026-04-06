from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import GoogleAccount
from app.services.audit import write_audit_log
from app.services.google_integration import sync_all_google_accounts
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.sync_tenant_google_accounts")
def sync_tenant_google_accounts(tenant_id: str) -> dict:
    tenant_uuid = UUID(tenant_id)
    db = SessionLocal()
    try:
        result = asyncio.run(sync_all_google_accounts(db, tenant_uuid))
        write_audit_log(
            db,
            tenant_id=tenant_uuid,
            actor_user_id=None,
            action="google.sync.scheduled",
            target_type="tenant",
            target_id=tenant_id,
            metadata={
                "connected_accounts": result.connected_accounts,
                "synced_locations": result.synced_locations,
                "synced_reviews": result.synced_reviews,
                "replies_posted": result.replies_posted,
                "errors": result.errors,
            },
        )
        db.commit()
        return {
            "tenant_id": tenant_id,
            "connected_accounts": result.connected_accounts,
            "synced_locations": result.synced_locations,
            "synced_reviews": result.synced_reviews,
            "replies_posted": result.replies_posted,
            "errors": result.errors,
        }
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.sync_all_google_accounts")
def sync_all_google_accounts_task() -> dict:
    db = SessionLocal()
    try:
        tenant_ids = db.scalars(
            select(GoogleAccount.tenant_id).where(GoogleAccount.is_active.is_(True)).distinct()
        ).all()
    finally:
        db.close()

    results = [sync_tenant_google_accounts.delay(str(tenant_id)).id for tenant_id in tenant_ids]
    return {"queued_tenants": len(tenant_ids), "task_ids": results}

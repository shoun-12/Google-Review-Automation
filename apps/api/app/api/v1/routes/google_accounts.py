from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from urllib.parse import quote

from app.core.config import settings
from app.api.deps import require_master_admin
from app.db.session import get_db
from app.models.entities import Membership
from app.schemas.google_accounts import GoogleAccountListResponse
from app.schemas.google_oauth import GoogleOAuthStartResponse
from app.schemas.google_oauth import GoogleSyncResponse
from app.services.audit import write_audit_log
from app.services.dashboard import list_google_accounts
from app.services.google_integration import build_google_authorization_url
from app.services.google_integration import create_oauth_state
from app.services.google_integration import handle_google_oauth_callback
from app.services.google_integration import sync_all_google_accounts


router = APIRouter()


async def process_google_oauth_callback(db: Session, code: str, state: str) -> RedirectResponse:
    try:
        connected_count = await handle_google_oauth_callback(db, code, state)
        write_audit_log(
            db,
            tenant_id=None,
            actor_user_id=None,
            action="google.oauth.completed",
            target_type="oauth_state",
            metadata={"connected_accounts": connected_count},
        )
        db.commit()
        redirect_url = f"{settings.web_base_url}/?google_oauth=success"
    except Exception as exc:
        redirect_url = f"{settings.web_base_url}/?google_oauth=error&message={quote(str(exc))}"

    return RedirectResponse(url=redirect_url, status_code=302)


@router.get("", response_model=GoogleAccountListResponse)
def get_google_accounts(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> GoogleAccountListResponse:
    return GoogleAccountListResponse(items=list_google_accounts(db, membership.tenant_id))


@router.post("/sync", response_model=GoogleSyncResponse)
async def sync_google_accounts(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> GoogleSyncResponse:
    try:
        result = await sync_all_google_accounts(db, membership.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="google.sync.triggered",
        target_type="tenant",
        target_id=str(membership.tenant_id),
        metadata={
            "connected_accounts": result.connected_accounts,
            "synced_locations": result.synced_locations,
            "synced_reviews": result.synced_reviews,
            "replies_posted": result.replies_posted,
            "errors": result.errors,
        },
    )
    db.commit()

    return GoogleSyncResponse(
        message="Google Business Profile sync completed",
        connected_accounts=result.connected_accounts,
        synced_locations=result.synced_locations,
        synced_reviews=result.synced_reviews,
        replies_posted=result.replies_posted,
        errors=result.errors,
    )


@router.post("/oauth/start", response_model=GoogleOAuthStartResponse)
def start_google_oauth(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> GoogleOAuthStartResponse:
    try:
        state_token = create_oauth_state(db, membership)
        authorization_url = build_google_authorization_url(state_token)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="google.oauth.started",
        target_type="tenant",
        target_id=str(membership.tenant_id),
        metadata={},
    )
    db.commit()

    return GoogleOAuthStartResponse(authorization_url=authorization_url)


@router.get("/oauth/callback", include_in_schema=False)
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    return await process_google_oauth_callback(db, code, state)

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership
from app.api.deps import require_master_admin
from app.db.session import get_db
from app.models.entities import GBPProfile
from app.models.entities import Membership
from app.models.entities import RoleEnum
from app.models.entities import User
from app.schemas.profiles import ProfileListResponse
from app.schemas.profiles import ProfileListItem
from app.schemas.profiles import ProfileUpdateRequest
from app.services.audit import write_audit_log
from app.services.dashboard import list_profiles

router = APIRouter()


@router.get("", response_model=ProfileListResponse)
def get_profiles(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> ProfileListResponse:
    return ProfileListResponse(
        items=list_profiles(
            db,
            membership.tenant_id,
            user_id=membership.user_id,
            role=membership.role,
        )
    )


@router.patch("/{profile_id}", response_model=ProfileListItem)
def update_profile(
    profile_id: UUID,
    payload: ProfileUpdateRequest,
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> ProfileListItem:
    profile = db.scalar(
        select(GBPProfile).where(
            GBPProfile.id == profile_id,
            GBPProfile.tenant_id == membership.tenant_id,
            GBPProfile.deleted_at.is_(None),
        )
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    if "primary_local_admin_user_id" in payload.model_fields_set:
        if payload.primary_local_admin_user_id is None:
            profile.primary_local_admin_user_id = None
        else:
            admin_user = db.get(User, payload.primary_local_admin_user_id)
            admin_membership = db.scalar(
                select(Membership).where(
                    Membership.tenant_id == membership.tenant_id,
                    Membership.user_id == payload.primary_local_admin_user_id,
                )
            )
            if admin_user is None or admin_membership is None:
                raise HTTPException(status_code=404, detail="Assigned local admin not found")
            if admin_membership.role not in {RoleEnum.LOCAL_ADMIN, RoleEnum.MASTER_ADMIN}:
                raise HTTPException(status_code=400, detail="Assigned user does not have an allowed role")
            profile.primary_local_admin_user_id = admin_user.id
    if payload.auto_respond_enabled is not None:
        profile.auto_respond_enabled = payload.auto_respond_enabled
    if payload.is_active is not None:
        profile.is_active = payload.is_active

    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="profile.updated",
        target_type="gbp_profile",
        target_id=str(profile.id),
        metadata={
            "primary_local_admin_user_id": (
                str(profile.primary_local_admin_user_id) if profile.primary_local_admin_user_id else None
            ),
            "auto_respond_enabled": profile.auto_respond_enabled,
            "is_active": profile.is_active,
        },
    )
    db.commit()
    db.refresh(profile)
    admin_name = None
    if profile.primary_local_admin_user_id:
        admin = db.get(User, profile.primary_local_admin_user_id)
        admin_name = admin.full_name if admin else None

    return ProfileListItem(
        id=profile.id,
        business_name=profile.business_name,
        city=profile.city,
        state=profile.state,
        brand=profile.brand.value,
        avg_rating_cached=float(profile.avg_rating_cached),
        total_reviews_cached=profile.total_reviews_cached,
        auto_respond_enabled=profile.auto_respond_enabled,
        is_active=profile.is_active,
        last_review_activity_at=profile.last_review_activity_at,
        primary_local_admin_user_id=profile.primary_local_admin_user_id,
        primary_local_admin_name=admin_name,
    )

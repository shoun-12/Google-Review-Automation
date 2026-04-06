from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_master_admin
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.entities import Membership
from app.models.entities import RoleEnum
from app.models.entities import User
from app.schemas.users import UserCreateRequest
from app.schemas.users import UserListItem
from app.schemas.users import UserListResponse
from app.schemas.users import UserUpdateRequest
from app.services.audit import write_audit_log
from app.services.dashboard import list_users


router = APIRouter()


@router.get("", response_model=UserListResponse)
def get_users(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> UserListResponse:
    return UserListResponse(items=list_users(db, membership.tenant_id))


@router.post("", response_model=UserListItem, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> UserListItem:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    try:
        role = RoleEnum(payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid role") from exc
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()

    user_membership = Membership(
        tenant_id=membership.tenant_id,
        user_id=user.id,
        role=role,
        email_alerts_enabled=payload.email_alerts_enabled,
        whatsapp_alerts_enabled=payload.whatsapp_alerts_enabled,
        invited_by_user_id=membership.user_id,
    )
    db.add(user_membership)
    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="user.created",
        target_type="user",
        target_id=str(user.id),
        metadata={"role": role.value, "email": user.email},
    )
    db.commit()
    db.refresh(user)
    db.refresh(user_membership)

    return UserListItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active and user_membership.is_active,
        role=user_membership.role.value,
        email_alerts_enabled=user_membership.email_alerts_enabled,
        whatsapp_alerts_enabled=user_membership.whatsapp_alerts_enabled,
        last_login_at=user.last_login_at,
        joined_at=user_membership.created_at,
    )


@router.patch("/{user_id}", response_model=UserListItem)
def update_user(
    user_id: UUID,
    payload: UserUpdateRequest,
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> UserListItem:
    user = db.scalar(
        select(User)
        .join(Membership, Membership.user_id == User.id)
        .where(User.id == user_id, Membership.tenant_id == membership.tenant_id)
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user_membership = db.scalar(
        select(Membership).where(Membership.tenant_id == membership.tenant_id, Membership.user_id == user.id)
    )
    if user_membership is None:
        raise HTTPException(status_code=404, detail="Membership not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone_number is not None:
        user.phone_number = payload.phone_number
    if payload.is_active is not None:
        user.is_active = payload.is_active
        user_membership.is_active = payload.is_active
    if payload.role is not None:
        try:
            user_membership.role = RoleEnum(payload.role)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid role") from exc
    if payload.email_alerts_enabled is not None:
        user_membership.email_alerts_enabled = payload.email_alerts_enabled
    if payload.whatsapp_alerts_enabled is not None:
        user_membership.whatsapp_alerts_enabled = payload.whatsapp_alerts_enabled

    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="user.updated",
        target_type="user",
        target_id=str(user.id),
        metadata={
            "role": user_membership.role.value,
            "is_active": user.is_active,
            "email_alerts_enabled": user_membership.email_alerts_enabled,
            "whatsapp_alerts_enabled": user_membership.whatsapp_alerts_enabled,
        },
    )
    db.commit()
    db.refresh(user)
    db.refresh(user_membership)

    return UserListItem(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=user.is_active and user_membership.is_active,
        role=user_membership.role.value,
        email_alerts_enabled=user_membership.email_alerts_enabled,
        whatsapp_alerts_enabled=user_membership.whatsapp_alerts_enabled,
        last_login_at=user.last_login_at,
        joined_at=user_membership.created_at,
    )

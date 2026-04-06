from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.entities import Membership
from app.models.entities import RoleEnum
from app.models.entities import Tenant
from app.models.entities import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = UUID(payload["sub"])
    except Exception as exc:  # pragma: no cover
        raise credentials_error from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise credentials_error

    return user


def get_current_membership(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    membership = db.scalar(
        select(Membership)
        .where(Membership.user_id == current_user.id, Membership.is_active.is_(True))
        .order_by(Membership.created_at.asc())
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to an active tenant",
        )
    return membership


def get_current_tenant(
    membership: Membership = Depends(get_current_membership),
    db: Session = Depends(get_db),
) -> Tenant:
    tenant = db.get(Tenant, membership.tenant_id)
    if tenant is None or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant is not active",
        )
    return tenant


def require_master_admin(membership: Membership = Depends(get_current_membership)) -> Membership:
    if membership.role != RoleEnum.MASTER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Master admin access is required",
        )
    return membership

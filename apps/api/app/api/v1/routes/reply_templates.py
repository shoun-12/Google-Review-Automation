from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import require_master_admin
from app.db.session import get_db
from app.models.entities import BrandEnum
from app.models.entities import Membership
from app.models.entities import ReplyTemplate
from app.models.entities import ReviewSentimentEnum
from app.schemas.templates import ReplyTemplateListResponse
from app.schemas.templates import ReplyTemplateListItem
from app.schemas.templates import ReplyTemplateUpsertRequest
from app.services.audit import write_audit_log
from app.services.dashboard import list_reply_templates


router = APIRouter()


@router.get("", response_model=ReplyTemplateListResponse)
def get_reply_templates(
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> ReplyTemplateListResponse:
    return ReplyTemplateListResponse(items=list_reply_templates(db, membership.tenant_id))


@router.post("", response_model=ReplyTemplateListItem)
def create_reply_template(
    payload: ReplyTemplateUpsertRequest,
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> ReplyTemplateListItem:
    try:
        brand = BrandEnum(payload.brand)
        sentiment = ReviewSentimentEnum(payload.sentiment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid brand or sentiment") from exc

    existing = db.scalar(
        select(ReplyTemplate).where(
            ReplyTemplate.tenant_id == membership.tenant_id,
            ReplyTemplate.brand == brand,
            ReplyTemplate.sentiment == sentiment,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=400, detail="Template already exists for this brand and sentiment")

    template = ReplyTemplate(
        tenant_id=membership.tenant_id,
        brand=brand,
        sentiment=sentiment,
        template_text=payload.template_text,
        is_active=payload.is_active,
        updated_by_user_id=membership.user_id,
    )
    db.add(template)
    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="reply_template.created",
        target_type="reply_template",
        metadata={"brand": brand.value, "sentiment": sentiment.value},
    )
    db.commit()
    db.refresh(template)
    return ReplyTemplateListItem(
        id=template.id,
        brand=template.brand.value,
        sentiment=template.sentiment.value,
        template_text=template.template_text,
        is_active=template.is_active,
    )


@router.patch("/{template_id}", response_model=ReplyTemplateListItem)
def update_reply_template(
    template_id: UUID,
    payload: ReplyTemplateUpsertRequest,
    membership: Membership = Depends(require_master_admin),
    db: Session = Depends(get_db),
) -> ReplyTemplateListItem:
    template = db.scalar(
        select(ReplyTemplate).where(
            ReplyTemplate.id == template_id,
            ReplyTemplate.tenant_id == membership.tenant_id,
        )
    )
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        template.brand = BrandEnum(payload.brand)
        template.sentiment = ReviewSentimentEnum(payload.sentiment)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid brand or sentiment") from exc

    template.template_text = payload.template_text
    template.is_active = payload.is_active
    template.updated_by_user_id = membership.user_id
    write_audit_log(
        db,
        tenant_id=membership.tenant_id,
        actor_user_id=membership.user_id,
        action="reply_template.updated",
        target_type="reply_template",
        target_id=str(template.id),
        metadata={"brand": template.brand.value, "sentiment": template.sentiment.value},
    )
    db.commit()
    db.refresh(template)
    return ReplyTemplateListItem(
        id=template.id,
        brand=template.brand.value,
        sentiment=template.sentiment.value,
        template_text=template.template_text,
        is_active=template.is_active,
    )

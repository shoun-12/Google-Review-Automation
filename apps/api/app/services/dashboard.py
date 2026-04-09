from __future__ import annotations

from uuid import UUID

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AlertLog
from app.models.entities import AlertStatusEnum
from app.models.entities import AuditLog
from app.models.entities import GBPProfile
from app.models.entities import GoogleAccount
from app.models.entities import Membership
from app.models.entities import RoleEnum
from app.models.entities import Reply
from app.models.entities import ReplyTemplate
from app.models.entities import Review
from app.models.entities import ReviewSentimentEnum
from app.models.entities import User
from app.schemas.dashboard import DashboardResponse
from app.schemas.dashboard import DashboardSyncStatus
from app.schemas.google_accounts import GoogleAccountListItem
from app.schemas.profiles import ProfileListItem
from app.schemas.reports import SummaryReportResponse
from app.schemas.reviews import ReviewListItem
from app.schemas.reviews import ReviewListResponse
from app.schemas.templates import ReplyTemplateListItem
from app.schemas.users import UserListItem


def _profile_scope_filters(tenant_id: UUID, user_id: UUID | None, role: RoleEnum | None) -> list:
    filters = [
        GBPProfile.tenant_id == tenant_id,
        GBPProfile.deleted_at.is_(None),
    ]
    if role == RoleEnum.LOCAL_ADMIN and user_id is not None:
        filters.append(GBPProfile.primary_local_admin_user_id == user_id)
    return filters


def _review_scope_filters(tenant_id: UUID, user_id: UUID | None, role: RoleEnum | None) -> list:
    filters = [
        Review.tenant_id == tenant_id,
        Review.deleted_at.is_(None),
    ]
    if role == RoleEnum.LOCAL_ADMIN and user_id is not None:
        filters.append(GBPProfile.primary_local_admin_user_id == user_id)
    return filters


def _review_feed_filters(
    tenant_id: UUID,
    user_id: UUID | None,
    role: RoleEnum | None,
    sentiment: ReviewSentimentEnum | None = None,
    profile_id: UUID | None = None,
) -> list:
    filters = _review_scope_filters(tenant_id, user_id, role)
    if sentiment is not None:
        filters.append(Review.sentiment == sentiment)
    if profile_id is not None:
        filters.append(Review.gbp_profile_id == profile_id)
    return filters


def _review_listing_query(
    tenant_id: UUID,
    user_id: UUID | None,
    role: RoleEnum | None,
    sentiment: ReviewSentimentEnum | None = None,
    profile_id: UUID | None = None,
):
    return (
        select(Review, GBPProfile.business_name, Reply.reply_text)
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .outerjoin(Reply, Reply.review_id == Review.id)
        .where(*_review_feed_filters(tenant_id, user_id, role, sentiment=sentiment, profile_id=profile_id))
    )


def get_summary(
    db: Session,
    tenant_id: UUID,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
) -> SummaryReportResponse:
    profile_filters = _profile_scope_filters(tenant_id, user_id, role)
    review_filters = _review_scope_filters(tenant_id, user_id, role)

    total_profiles = db.scalar(
        select(func.count(GBPProfile.id)).where(*profile_filters)
    ) or 0
    reviews_received = db.scalar(
        select(func.count(Review.id)).join(GBPProfile, GBPProfile.id == Review.gbp_profile_id).where(*review_filters)
    ) or 0
    positive_reviews = db.scalar(
        select(func.count(Review.id))
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .where(
            *review_filters,
            )
        .where(Review.sentiment == ReviewSentimentEnum.POSITIVE)
    ) or 0
    negative_reviews = db.scalar(
        select(func.count(Review.id))
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .where(
            *review_filters,
        )
        .where(Review.sentiment == ReviewSentimentEnum.NEGATIVE)
    ) or 0
    replies_posted = db.scalar(
        select(func.count(Reply.id))
        .join(Review, Reply.review_id == Review.id)
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .where(*review_filters)
    ) or 0
    alerts_total = db.scalar(select(func.count(AlertLog.id)).where(AlertLog.tenant_id == tenant_id)) or 0
    alerts_sent = db.scalar(
        select(func.count(AlertLog.id)).where(
            AlertLog.tenant_id == tenant_id,
            AlertLog.status == AlertStatusEnum.SENT,
        )
    ) or 0
    average_rating = db.scalar(
        select(func.coalesce(func.avg(Review.star_rating), 0))
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .where(*review_filters)
    ) or 0

    return SummaryReportResponse(
        total_connected_profiles=int(total_profiles),
        reviews_received=int(reviews_received),
        positive_reviews=int(positive_reviews),
        negative_reviews=int(negative_reviews),
        ai_response_rate=round((replies_posted / reviews_received) if reviews_received else 0, 2),
        alert_delivery_rate=round((alerts_sent / alerts_total) if alerts_total else 0, 2),
        average_rating_network=round(float(average_rating), 2),
    )


def list_users(db: Session, tenant_id) -> list[UserListItem]:
    rows = db.execute(
        select(User, Membership)
        .join(Membership, Membership.user_id == User.id)
        .where(Membership.tenant_id == tenant_id)
        .order_by(User.full_name.asc())
    ).all()
    return [
        UserListItem(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            phone_number=user.phone_number,
            is_active=user.is_active and membership.is_active,
            role=membership.role.value,
            email_alerts_enabled=membership.email_alerts_enabled,
            whatsapp_alerts_enabled=membership.whatsapp_alerts_enabled,
            last_login_at=user.last_login_at,
            joined_at=membership.created_at,
        )
        for user, membership in rows
    ]


def list_profiles(
    db: Session,
    tenant_id: UUID,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
) -> list[ProfileListItem]:
    rows = db.execute(
        select(GBPProfile, User.full_name)
        .outerjoin(User, User.id == GBPProfile.primary_local_admin_user_id)
        .where(*_profile_scope_filters(tenant_id, user_id, role))
        .order_by(GBPProfile.business_name.asc())
    ).all()
    return [
        ProfileListItem(
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
        for profile, admin_name in rows
    ]


def list_reviews(
    db: Session,
    tenant_id: UUID,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
    limit: int = 20,
) -> list[ReviewListItem]:
    rows = db.execute(
        _review_listing_query(tenant_id, user_id, role)
        .order_by(Review.review_posted_at.desc())
        .limit(limit)
    ).all()
    return [
        ReviewListItem(
            id=review.id,
            gbp_review_id=review.gbp_review_id,
            business_name=business_name,
            reviewer_name=review.reviewer_name,
            star_rating=review.star_rating,
            review_text=review.review_text,
            sentiment=review.sentiment.value,
            status=review.status.value,
            review_posted_at=review.review_posted_at,
            reply_text=reply_text,
        )
        for review, business_name, reply_text in rows
    ]


def list_review_feed(
    db: Session,
    tenant_id: UUID,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
    sentiment: ReviewSentimentEnum | None = None,
    profile_id: UUID | None = None,
    page: int = 1,
    page_size: int = 5,
) -> ReviewListResponse:
    safe_page = max(page, 1)
    safe_page_size = min(max(page_size, 1), 50)
    filters = _review_feed_filters(tenant_id, user_id, role, sentiment=sentiment, profile_id=profile_id)

    total = db.scalar(
        select(func.count(func.distinct(Review.id)))
        .select_from(Review)
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .where(*filters)
    ) or 0
    rows = db.execute(
        _review_listing_query(tenant_id, user_id, role, sentiment=sentiment, profile_id=profile_id)
        .order_by(Review.review_posted_at.desc(), Review.created_at.desc())
        .offset((safe_page - 1) * safe_page_size)
        .limit(safe_page_size)
    ).all()
    total_pages = ((int(total) - 1) // safe_page_size) + 1 if total else 0
    items = [
        ReviewListItem(
            id=review.id,
            gbp_review_id=review.gbp_review_id,
            business_name=business_name,
            reviewer_name=review.reviewer_name,
            star_rating=review.star_rating,
            review_text=review.review_text,
            sentiment=review.sentiment.value,
            status=review.status.value,
            review_posted_at=review.review_posted_at,
            reply_text=reply_text,
        )
        for review, business_name, reply_text in rows
    ]
    return ReviewListResponse(
        items=items,
        total=int(total),
        page=safe_page,
        page_size=safe_page_size,
        total_pages=total_pages,
    )


def list_google_accounts(db: Session, tenant_id) -> list[GoogleAccountListItem]:
    rows = db.scalars(
        select(GoogleAccount).where(GoogleAccount.tenant_id == tenant_id).order_by(GoogleAccount.created_at.asc())
    ).all()
    return [GoogleAccountListItem.model_validate(item) for item in rows]


def list_reply_templates(db: Session, tenant_id) -> list[ReplyTemplateListItem]:
    rows = db.scalars(
        select(ReplyTemplate).where(ReplyTemplate.tenant_id == tenant_id).order_by(ReplyTemplate.brand.asc())
    ).all()
    return [
        ReplyTemplateListItem(
            id=item.id,
            brand=item.brand.value,
            sentiment=item.sentiment.value,
            template_text=item.template_text,
            is_active=item.is_active,
        )
        for item in rows
    ]


def get_latest_sync_status(db: Session, tenant_id: UUID) -> DashboardSyncStatus | None:
    log = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action.in_(["google.sync.triggered", "google.sync.scheduled"]),
        )
        .order_by(AuditLog.created_at.desc())
    )
    if log is None:
        return None
    return DashboardSyncStatus(
        action=log.action,
        created_at=log.created_at,
        metadata_json=log.metadata_json,
    )


def get_dashboard_payload(
    db: Session,
    tenant_id: UUID,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
) -> DashboardResponse:
    return DashboardResponse(
        summary=get_summary(db, tenant_id, user_id=user_id, role=role),
        profiles=list_profiles(db, tenant_id, user_id=user_id, role=role)[:8],
        reviews=list_reviews(db, tenant_id, user_id=user_id, role=role, limit=8),
        users=list_users(db, tenant_id)[:8],
        google_accounts=list_google_accounts(db, tenant_id)[:8],
        reply_templates=list_reply_templates(db, tenant_id)[:8],
        latest_sync=get_latest_sync_status(db, tenant_id),
    )

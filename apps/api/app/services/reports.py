from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta
from uuid import UUID

from sqlalchemy import case
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import GBPProfile
from app.models.entities import Reply
from app.models.entities import Review
from app.models.entities import ReviewSentimentEnum
from app.models.entities import RoleEnum
from app.schemas.reports import ProfilePerformanceItem
from app.schemas.reports import ReportOverviewResponse
from app.schemas.reports import SummaryReportResponse
from app.schemas.reports import TrendPoint
from app.services.dashboard import get_summary


@dataclass
class ReportFilters:
    tenant_id: UUID
    start_at: datetime
    end_at: datetime
    user_id: UUID | None = None
    role: RoleEnum | None = None


def build_report_filters(
    tenant_id: UUID,
    days: int,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
) -> ReportFilters:
    safe_days = min(max(days, 1), 90)
    end_at = datetime.now(UTC)
    start_at = end_at - timedelta(days=safe_days - 1)
    start_at = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
    end_at = end_at.replace(hour=23, minute=59, second=59, microsecond=999999)
    return ReportFilters(
        tenant_id=tenant_id,
        start_at=start_at,
        end_at=end_at,
        user_id=user_id,
        role=role,
    )


def _scoped_profile_filters(filters: ReportFilters) -> list:
    scoped_filters = [
        GBPProfile.tenant_id == filters.tenant_id,
        GBPProfile.deleted_at.is_(None),
    ]
    if filters.role == RoleEnum.LOCAL_ADMIN and filters.user_id is not None:
        scoped_filters.append(GBPProfile.primary_local_admin_user_id == filters.user_id)
    return scoped_filters


def _scoped_review_filters(filters: ReportFilters) -> list:
    scoped_filters = [
        Review.tenant_id == filters.tenant_id,
        Review.deleted_at.is_(None),
        Review.review_posted_at >= filters.start_at,
        Review.review_posted_at <= filters.end_at,
    ]
    if filters.role == RoleEnum.LOCAL_ADMIN and filters.user_id is not None:
        scoped_filters.append(GBPProfile.primary_local_admin_user_id == filters.user_id)
    return scoped_filters


def _trend_lookup(db: Session, filters: ReportFilters) -> dict[date, TrendPoint]:
    rows = db.execute(
        select(
            func.date(Review.review_posted_at).label("day"),
            func.count(Review.id).label("reviews_received"),
            func.sum(
                case((Review.sentiment == ReviewSentimentEnum.POSITIVE, 1), else_=0)
            ).label("positive_reviews"),
            func.sum(
                case((Review.sentiment == ReviewSentimentEnum.NEGATIVE, 1), else_=0)
            ).label("negative_reviews"),
            func.count(Reply.id).label("replies_posted"),
            func.coalesce(func.avg(Review.star_rating), 0).label("avg_rating"),
        )
        .select_from(Review)
        .join(GBPProfile, GBPProfile.id == Review.gbp_profile_id)
        .outerjoin(Reply, Reply.review_id == Review.id)
        .where(*_scoped_review_filters(filters))
        .group_by(func.date(Review.review_posted_at))
        .order_by(func.date(Review.review_posted_at).asc())
    ).all()

    return {
        row.day: TrendPoint(
            date=row.day.isoformat(),
            reviews_received=int(row.reviews_received or 0),
            positive_reviews=int(row.positive_reviews or 0),
            negative_reviews=int(row.negative_reviews or 0),
            replies_posted=int(row.replies_posted or 0),
            avg_rating=round(float(row.avg_rating or 0), 2),
        )
        for row in rows
    }


def get_trend_points(db: Session, filters: ReportFilters) -> list[TrendPoint]:
    lookup = _trend_lookup(db, filters)
    points: list[TrendPoint] = []
    current_day = filters.start_at.date()
    end_day = filters.end_at.date()
    while current_day <= end_day:
        points.append(
            lookup.get(
                current_day,
                TrendPoint(
                    date=current_day.isoformat(),
                    reviews_received=0,
                    positive_reviews=0,
                    negative_reviews=0,
                    replies_posted=0,
                    avg_rating=0,
                ),
            )
        )
        current_day += timedelta(days=1)
    return points


def get_profile_performance(db: Session, filters: ReportFilters) -> list[ProfilePerformanceItem]:
    rows = db.execute(
        select(
            GBPProfile.id,
            GBPProfile.business_name,
            GBPProfile.brand,
            GBPProfile.city,
            GBPProfile.state,
            func.count(Review.id).label("reviews_received"),
            func.sum(
                case((Review.sentiment == ReviewSentimentEnum.POSITIVE, 1), else_=0)
            ).label("positive_reviews"),
            func.sum(
                case((Review.sentiment == ReviewSentimentEnum.NEGATIVE, 1), else_=0)
            ).label("negative_reviews"),
            func.count(Reply.id).label("replies_posted"),
            func.coalesce(func.avg(Review.star_rating), 0).label("avg_rating"),
        )
        .select_from(GBPProfile)
        .join(Review, Review.gbp_profile_id == GBPProfile.id)
        .outerjoin(Reply, Reply.review_id == Review.id)
        .where(
            *_scoped_profile_filters(filters),
            Review.deleted_at.is_(None),
            Review.review_posted_at >= filters.start_at,
            Review.review_posted_at <= filters.end_at,
        )
        .group_by(
            GBPProfile.id,
            GBPProfile.business_name,
            GBPProfile.brand,
            GBPProfile.city,
            GBPProfile.state,
        )
        .order_by(func.count(Review.id).desc(), GBPProfile.business_name.asc())
    ).all()

    items: list[ProfilePerformanceItem] = []
    for row in rows:
        reviews_received = int(row.reviews_received or 0)
        replies_posted = int(row.replies_posted or 0)
        items.append(
            ProfilePerformanceItem(
                id=str(row.id),
                business_name=row.business_name,
                brand=row.brand.value,
                city=row.city,
                state=row.state,
                reviews_received=reviews_received,
                positive_reviews=int(row.positive_reviews or 0),
                negative_reviews=int(row.negative_reviews or 0),
                replies_posted=replies_posted,
                avg_rating=round(float(row.avg_rating or 0), 2),
                response_rate=round((replies_posted / reviews_received) if reviews_received else 0, 2),
            )
        )
    return items


def get_report_overview(
    db: Session,
    tenant_id: UUID,
    days: int,
    user_id: UUID | None = None,
    role: RoleEnum | None = None,
) -> ReportOverviewResponse:
    filters = build_report_filters(tenant_id, days, user_id=user_id, role=role)
    summary = get_summary(db, tenant_id, user_id=user_id, role=role)
    trend = get_trend_points(db, filters)
    profiles = get_profile_performance(db, filters)
    return ReportOverviewResponse(
        summary=SummaryReportResponse.model_validate(summary),
        trend=trend,
        profiles=profiles,
        window_days=days if 1 <= days <= 90 else min(max(days, 1), 90),
    )


def build_profiles_csv(db: Session, tenant_id: UUID, days: int) -> str:
    filters = build_report_filters(tenant_id, days)
    rows = get_profile_performance(db, filters)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "business_name",
            "brand",
            "city",
            "state",
            "reviews_received",
            "positive_reviews",
            "negative_reviews",
            "replies_posted",
            "response_rate",
            "avg_rating",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row.business_name,
                row.brand,
                row.city or "",
                row.state or "",
                row.reviews_received,
                row.positive_reviews,
                row.negative_reviews,
                row.replies_posted,
                row.response_rate,
                row.avg_rating,
            ]
        )
    return buffer.getvalue()

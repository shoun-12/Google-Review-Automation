from __future__ import annotations

from datetime import date
from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import JSON
from sqlalchemy import Boolean
from sqlalchemy import Date
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteMixin
from app.models.base import TimestampedBase


def values_enum(enum_cls: type[Enum]) -> SQLAlchemyEnum:
    return SQLAlchemyEnum(
        enum_cls,
        name=f"{enum_cls.__name__.lower()}",
        values_callable=lambda items: [item.value for item in items],
    )


class RoleEnum(str, Enum):
    MASTER_ADMIN = "master_admin"
    LOCAL_ADMIN = "local_admin"


class BrandEnum(str, Enum):
    KUTTUKARAN = "kuttukaran"
    MARUTI = "maruti"
    OTHER = "other"


class ReviewSentimentEnum(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ReviewStatusEnum(str, Enum):
    PENDING = "pending"
    REPLIED = "replied"
    IGNORED = "ignored"
    FAILED = "failed"


class ReplyTypeEnum(str, Enum):
    AI_GENERATED = "ai_generated"
    TEMPLATED = "templated"
    MANUAL = "manual"


class AlertChannelEnum(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class AlertStatusEnum(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


role_enum_type = SQLAlchemyEnum(
    RoleEnum,
    name="role_enum",
    values_callable=lambda items: [item.value for item in items],
)
brand_enum_type = SQLAlchemyEnum(
    BrandEnum,
    name="brand_enum",
    values_callable=lambda items: [item.value for item in items],
)
review_sentiment_enum_type = SQLAlchemyEnum(
    ReviewSentimentEnum,
    name="review_sentiment_enum",
    values_callable=lambda items: [item.value for item in items],
)
review_status_enum_type = SQLAlchemyEnum(
    ReviewStatusEnum,
    name="review_status_enum",
    values_callable=lambda items: [item.value for item in items],
)
reply_type_enum_type = SQLAlchemyEnum(
    ReplyTypeEnum,
    name="reply_type_enum",
    values_callable=lambda items: [item.value for item in items],
)
alert_channel_enum_type = SQLAlchemyEnum(
    AlertChannelEnum,
    name="alert_channel_enum",
    values_callable=lambda items: [item.value for item in items],
)
alert_status_enum_type = SQLAlchemyEnum(
    AlertStatusEnum,
    name="alert_status_enum",
    values_callable=lambda items: [item.value for item in items],
)


class Tenant(TimestampedBase, SoftDeleteMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    website_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    memberships = relationship("Membership", back_populates="tenant")
    google_accounts = relationship("GoogleAccount", back_populates="tenant")
    profiles = relationship("GBPProfile", back_populates="tenant")
    reply_templates = relationship("ReplyTemplate", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")


class User(TimestampedBase):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships = relationship("Membership", back_populates="user", foreign_keys="Membership.user_id")
    connected_google_accounts = relationship("GoogleAccount", back_populates="connected_by_user")
    primary_profiles = relationship("GBPProfile", back_populates="primary_local_admin")
    profile_assignments = relationship(
        "ProfileAssignment",
        back_populates="user",
        foreign_keys="ProfileAssignment.user_id",
    )
    replies = relationship("Reply", back_populates="created_by_user")
    updated_templates = relationship("ReplyTemplate", back_populates="updated_by_user")
    alert_logs = relationship("AlertLog", back_populates="recipient_user")
    audit_logs = relationship("AuditLog", back_populates="actor_user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")


class Membership(TimestampedBase):
    __tablename__ = "memberships"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),)

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[RoleEnum] = mapped_column(role_enum_type, nullable=False)
    email_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    whatsapp_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    invited_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    tenant = relationship("Tenant", back_populates="memberships")
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])


class RefreshToken(TimestampedBase):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="refresh_tokens")


class OAuthState(TimestampedBase):
    __tablename__ = "oauth_states"

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    state_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class GoogleAccount(TimestampedBase):
    __tablename__ = "google_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_google_accounts_tenant_email"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    google_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    connected_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    tenant = relationship("Tenant", back_populates="google_accounts")
    connected_by_user = relationship("User", back_populates="connected_google_accounts")
    profiles = relationship("GBPProfile", back_populates="google_account")


class GBPProfile(TimestampedBase, SoftDeleteMixin):
    __tablename__ = "gbp_profiles"
    __table_args__ = (
        Index("ix_gbp_profiles_tenant_brand", "tenant_id", "brand"),
        Index("ix_gbp_profiles_tenant_active", "tenant_id", "is_active"),
        Index("ix_gbp_profiles_tenant_city", "tenant_id", "city"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    google_account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("google_accounts.id", ondelete="CASCADE"), nullable=False
    )
    primary_local_admin_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    gbp_location_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    store_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    brand: Mapped[BrandEnum] = mapped_column(brand_enum_type, nullable=False)
    avg_rating_cached: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0, server_default="0")
    total_reviews_cached: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_review_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_respond_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="profiles")
    google_account = relationship("GoogleAccount", back_populates="profiles")
    primary_local_admin = relationship(
        "User",
        back_populates="primary_profiles",
        foreign_keys=[primary_local_admin_user_id],
    )
    assignments = relationship("ProfileAssignment", back_populates="profile")
    reviews = relationship("Review", back_populates="profile")


class ProfileAssignment(TimestampedBase):
    __tablename__ = "profile_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "gbp_profile_id", name="uq_profile_assignments_user_profile"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    gbp_profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("gbp_profiles.id", ondelete="CASCADE"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    assigned_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    user = relationship("User", back_populates="profile_assignments", foreign_keys=[user_id])
    profile = relationship("GBPProfile", back_populates="assignments")


class Review(TimestampedBase, SoftDeleteMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_profile_posted_at", "gbp_profile_id", "review_posted_at"),
        Index("ix_reviews_profile_status", "gbp_profile_id", "status"),
        Index("ix_reviews_tenant_sentiment", "tenant_id", "sentiment"),
        Index("ix_reviews_tenant_posted_at", "tenant_id", "review_posted_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    gbp_profile_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("gbp_profiles.id", ondelete="CASCADE"), nullable=False
    )
    gbp_review_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    reviewer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    star_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[ReviewSentimentEnum] = mapped_column(review_sentiment_enum_type, nullable=False)
    status: Mapped[ReviewStatusEnum] = mapped_column(
        review_status_enum_type,
        nullable=False,
        default=ReviewStatusEnum.PENDING,
        server_default=ReviewStatusEnum.PENDING.value,
    )
    review_posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_payload_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    profile = relationship("GBPProfile", back_populates="reviews")
    reply = relationship("Reply", back_populates="review", uselist=False)
    alert_logs = relationship("AlertLog", back_populates="review")


class ReplyTemplate(TimestampedBase):
    __tablename__ = "reply_templates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "brand", "sentiment", name="uq_reply_templates_scope"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    brand: Mapped[BrandEnum] = mapped_column(brand_enum_type, nullable=False)
    sentiment: Mapped[ReviewSentimentEnum] = mapped_column(
        review_sentiment_enum_type, nullable=False
    )
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    updated_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    tenant = relationship("Tenant", back_populates="reply_templates")
    updated_by_user = relationship("User", back_populates="updated_templates")


class Reply(TimestampedBase):
    __tablename__ = "replies"

    review_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    reply_text: Mapped[str] = mapped_column(Text, nullable=False)
    reply_type: Mapped[ReplyTypeEnum] = mapped_column(reply_type_enum_type, nullable=False)
    generation_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    posted_to_google: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    review = relationship("Review", back_populates="reply")
    created_by_user = relationship("User", back_populates="replies")


class AlertLog(TimestampedBase):
    __tablename__ = "alert_logs"
    __table_args__ = (
        Index("ix_alert_logs_tenant_channel_status", "tenant_id", "channel", "status"),
        Index("ix_alert_logs_review_channel", "review_id", "channel"),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    review_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False
    )
    recipient_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    channel: Mapped[AlertChannelEnum] = mapped_column(alert_channel_enum_type, nullable=False)
    status: Mapped[AlertStatusEnum] = mapped_column(
        alert_status_enum_type,
        nullable=False,
        default=AlertStatusEnum.QUEUED,
        server_default=AlertStatusEnum.QUEUED.value,
    )
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    review = relationship("Review", back_populates="alert_logs")
    recipient_user = relationship("User", back_populates="alert_logs")


class AuditLog(TimestampedBase):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    tenant = relationship("Tenant", back_populates="audit_logs")
    actor_user = relationship("User", back_populates="audit_logs")


class AnalyticsDailySnapshot(TimestampedBase):
    __tablename__ = "analytics_daily_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "gbp_profile_id",
            "snapshot_date",
            name="uq_analytics_daily_snapshots_scope",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    gbp_profile_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("gbp_profiles.id", ondelete="SET NULL"), nullable=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    reviews_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    positive_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    negative_reviews: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    replies_posted: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    alerts_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    avg_rating: Mapped[float] = mapped_column(Numeric(3, 2), nullable=False, default=0, server_default="0")

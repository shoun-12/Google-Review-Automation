"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-04-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


role_enum = postgresql.ENUM("master_admin", "local_admin", name="role_enum", create_type=False)
brand_enum = postgresql.ENUM("kuttukaran", "maruti", "other", name="brand_enum", create_type=False)
review_sentiment_enum = postgresql.ENUM(
    "positive",
    "negative",
    "neutral",
    name="review_sentiment_enum",
    create_type=False,
)
review_status_enum = postgresql.ENUM(
    "pending",
    "replied",
    "ignored",
    "failed",
    name="review_status_enum",
    create_type=False,
)
reply_type_enum = postgresql.ENUM(
    "ai_generated",
    "templated",
    "manual",
    name="reply_type_enum",
    create_type=False,
)
alert_channel_enum = postgresql.ENUM("email", "whatsapp", name="alert_channel_enum", create_type=False)
alert_status_enum = postgresql.ENUM("queued", "sent", "failed", name="alert_status_enum", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    role_enum.create(bind, checkfirst=True)
    brand_enum.create(bind, checkfirst=True)
    review_sentiment_enum.create(bind, checkfirst=True)
    review_status_enum.create(bind, checkfirst=True)
    reply_type_enum.create(bind, checkfirst=True)
    alert_channel_enum.create(bind, checkfirst=True)
    alert_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "tenants",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("website_domain", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("is_platform_admin", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "oauth_states",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("state_token", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_token"),
    )
    op.create_table(
        "memberships",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("email_alerts_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("whatsapp_alerts_enabled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("invited_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["invited_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_memberships_tenant_user"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_jti", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_jti"),
    )
    op.create_table(
        "google_accounts",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("google_account_id", sa.String(length=255), nullable=True),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("token_last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("connected_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["connected_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_google_accounts_tenant_email"),
    )
    op.create_table(
        "gbp_profiles",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("google_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_local_admin_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("gbp_location_id", sa.String(length=255), nullable=False),
        sa.Column("business_name", sa.String(length=255), nullable=False),
        sa.Column("store_code", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("brand", brand_enum, nullable=False),
        sa.Column("avg_rating_cached", sa.Numeric(precision=3, scale=2), server_default="0", nullable=False),
        sa.Column("total_reviews_cached", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_review_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_respond_enabled", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["google_account_id"], ["google_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_local_admin_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gbp_location_id"),
    )
    op.create_index("ix_gbp_profiles_tenant_active", "gbp_profiles", ["tenant_id", "is_active"])
    op.create_index("ix_gbp_profiles_tenant_brand", "gbp_profiles", ["tenant_id", "brand"])
    op.create_index("ix_gbp_profiles_tenant_city", "gbp_profiles", ["tenant_id", "city"])
    op.create_table(
        "reply_templates",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("brand", brand_enum, nullable=False),
        sa.Column("sentiment", review_sentiment_enum, nullable=False),
        sa.Column("template_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("updated_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["updated_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "brand", "sentiment", name="uq_reply_templates_scope"),
    )
    op.create_table(
        "profile_assignments",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gbp_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("assigned_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["gbp_profile_id"], ["gbp_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "gbp_profile_id", name="uq_profile_assignments_user_profile"),
    )
    op.create_table(
        "reviews",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gbp_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gbp_review_id", sa.String(length=255), nullable=False),
        sa.Column("reviewer_name", sa.String(length=255), nullable=True),
        sa.Column("star_rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("sentiment", review_sentiment_enum, nullable=False),
        sa.Column("status", review_status_enum, server_default="pending", nullable=False),
        sa.Column("review_posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload_json", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["gbp_profile_id"], ["gbp_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gbp_review_id"),
    )
    op.create_index("ix_reviews_profile_posted_at", "reviews", ["gbp_profile_id", "review_posted_at"])
    op.create_index("ix_reviews_profile_status", "reviews", ["gbp_profile_id", "status"])
    op.create_index("ix_reviews_tenant_posted_at", "reviews", ["tenant_id", "review_posted_at"])
    op.create_index("ix_reviews_tenant_sentiment", "reviews", ["tenant_id", "sentiment"])
    op.create_table(
        "replies",
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reply_text", sa.Text(), nullable=False),
        sa.Column("reply_type", reply_type_enum, nullable=False),
        sa.Column("generation_model", sa.String(length=100), nullable=True),
        sa.Column("posted_to_google", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("review_id"),
    )
    op.create_table(
        "alert_logs",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel", alert_channel_enum, nullable=False),
        sa.Column("status", alert_status_enum, server_default="queued", nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["review_id"], ["reviews.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_alert_logs_tenant_channel_status",
        "alert_logs",
        ["tenant_id", "channel", "status"],
    )
    op.create_index("ix_alert_logs_review_channel", "alert_logs", ["review_id", "channel"])
    op.create_table(
        "audit_logs",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_type", sa.String(length=100), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_action_created", "audit_logs", ["action", "created_at"])
    op.create_index("ix_audit_logs_tenant_created", "audit_logs", ["tenant_id", "created_at"])
    op.create_table(
        "analytics_daily_snapshots",
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gbp_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("reviews_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("positive_reviews", sa.Integer(), server_default="0", nullable=False),
        sa.Column("negative_reviews", sa.Integer(), server_default="0", nullable=False),
        sa.Column("replies_posted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("alerts_sent", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_rating", sa.Numeric(precision=3, scale=2), server_default="0", nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["gbp_profile_id"], ["gbp_profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "gbp_profile_id",
            "snapshot_date",
            name="uq_analytics_daily_snapshots_scope",
        ),
    )


def downgrade() -> None:
    op.drop_table("analytics_daily_snapshots")
    op.drop_index("ix_audit_logs_tenant_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_alert_logs_review_channel", table_name="alert_logs")
    op.drop_index("ix_alert_logs_tenant_channel_status", table_name="alert_logs")
    op.drop_table("alert_logs")
    op.drop_table("replies")
    op.drop_index("ix_reviews_tenant_sentiment", table_name="reviews")
    op.drop_index("ix_reviews_tenant_posted_at", table_name="reviews")
    op.drop_index("ix_reviews_profile_status", table_name="reviews")
    op.drop_index("ix_reviews_profile_posted_at", table_name="reviews")
    op.drop_table("reviews")
    op.drop_table("profile_assignments")
    op.drop_table("reply_templates")
    op.drop_index("ix_gbp_profiles_tenant_city", table_name="gbp_profiles")
    op.drop_index("ix_gbp_profiles_tenant_brand", table_name="gbp_profiles")
    op.drop_index("ix_gbp_profiles_tenant_active", table_name="gbp_profiles")
    op.drop_table("gbp_profiles")
    op.drop_table("google_accounts")
    op.drop_table("refresh_tokens")
    op.drop_table("memberships")
    op.drop_table("oauth_states")
    op.drop_table("users")
    op.drop_table("tenants")

    bind = op.get_bind()
    alert_status_enum.drop(bind, checkfirst=True)
    alert_channel_enum.drop(bind, checkfirst=True)
    reply_type_enum.drop(bind, checkfirst=True)
    review_status_enum.drop(bind, checkfirst=True)
    review_sentiment_enum.drop(bind, checkfirst=True)
    brand_enum.drop(bind, checkfirst=True)
    role_enum.drop(bind, checkfirst=True)

from __future__ import annotations

import sys
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from sqlalchemy import select

SCRIPT_ROOT = Path(__file__).resolve().parent
CANDIDATE_API_ROOTS = [
    SCRIPT_ROOT.parent / "apps" / "api",
    Path("/app"),
]
for candidate in CANDIDATE_API_ROOTS:
    if candidate.exists():
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)
        break

from app.core.security import get_password_hash  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.entities import AlertChannelEnum  # noqa: E402
from app.models.entities import AlertLog  # noqa: E402
from app.models.entities import AlertStatusEnum  # noqa: E402
from app.models.entities import BrandEnum  # noqa: E402
from app.models.entities import GBPProfile  # noqa: E402
from app.models.entities import GoogleAccount  # noqa: E402
from app.models.entities import Membership  # noqa: E402
from app.models.entities import Reply  # noqa: E402
from app.models.entities import ReplyTemplate  # noqa: E402
from app.models.entities import ReplyTypeEnum  # noqa: E402
from app.models.entities import RoleEnum  # noqa: E402
from app.models.entities import Review  # noqa: E402
from app.models.entities import ReviewSentimentEnum  # noqa: E402
from app.models.entities import ReviewStatusEnum  # noqa: E402
from app.models.entities import Tenant  # noqa: E402
from app.models.entities import User  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "kuttukaran"))
        if tenant is None:
            tenant = Tenant(name="Kuttukaran", slug="kuttukaran")
            db.add(tenant)
            db.flush()

        user = db.scalar(select(User).where(User.email == "admin@example.com"))
        if user is None:
            user = User(
                email="admin@example.com",
                full_name="Master Admin",
                password_hash=get_password_hash("ChangeMe123!"),
                is_active=True,
            )
            db.add(user)
            db.flush()

        membership = db.scalar(
            select(Membership).where(
                Membership.tenant_id == tenant.id,
                Membership.user_id == user.id,
            )
        )
        if membership is None:
            db.add(
                Membership(
                    tenant_id=tenant.id,
                    user_id=user.id,
                    role=RoleEnum.MASTER_ADMIN,
                    email_alerts_enabled=True,
                    whatsapp_alerts_enabled=True,
                )
            )

        local_admin = db.scalar(select(User).where(User.email == "branch.manager@example.com"))
        if local_admin is None:
            local_admin = User(
                email="branch.manager@example.com",
                full_name="Branch Manager",
                phone_number="+919999999999",
                password_hash=get_password_hash("ChangeMe123!"),
                is_active=True,
            )
            db.add(local_admin)
            db.flush()

        local_membership = db.scalar(
            select(Membership).where(
                Membership.tenant_id == tenant.id,
                Membership.user_id == local_admin.id,
            )
        )
        if local_membership is None:
            db.add(
                Membership(
                    tenant_id=tenant.id,
                    user_id=local_admin.id,
                    role=RoleEnum.LOCAL_ADMIN,
                    email_alerts_enabled=True,
                    whatsapp_alerts_enabled=True,
                    invited_by_user_id=user.id,
                )
            )

        google_account = db.scalar(
            select(GoogleAccount).where(
                GoogleAccount.tenant_id == tenant.id,
                GoogleAccount.email == "profiles@kuttukaran.com",
            )
        )
        if google_account is None:
            google_account = GoogleAccount(
                tenant_id=tenant.id,
                email="profiles@kuttukaran.com",
                google_account_id="google-account-001",
                encrypted_refresh_token="encrypted-placeholder-token",
                scopes_json=[
                    "https://www.googleapis.com/auth/business.manage",
                ],
                connected_by_user_id=user.id,
                is_active=False,
            )
            db.add(google_account)
            db.flush()
        else:
            google_account.is_active = False

        profiles_data = [
            {
                "gbp_location_id": "loc-kochi-maruti-001",
                "business_name": "Maruti Arena Kochi",
                "city": "Kochi",
                "state": "Kerala",
                "brand": BrandEnum.MARUTI,
                "avg_rating_cached": 4.6,
                "total_reviews_cached": 186,
            },
            {
                "gbp_location_id": "loc-thrissur-kuttukaran-001",
                "business_name": "Kuttukaran Cars Thrissur",
                "city": "Thrissur",
                "state": "Kerala",
                "brand": BrandEnum.KUTTUKARAN,
                "avg_rating_cached": 4.1,
                "total_reviews_cached": 98,
            },
            {
                "gbp_location_id": "loc-trivandrum-maruti-001",
                "business_name": "Maruti Service Trivandrum",
                "city": "Thiruvananthapuram",
                "state": "Kerala",
                "brand": BrandEnum.MARUTI,
                "avg_rating_cached": 3.9,
                "total_reviews_cached": 121,
            },
        ]
        created_profiles: list[GBPProfile] = []
        for item in profiles_data:
            profile = db.scalar(
                select(GBPProfile).where(GBPProfile.gbp_location_id == item["gbp_location_id"])
            )
            if profile is None:
                profile = GBPProfile(
                    tenant_id=tenant.id,
                    google_account_id=google_account.id,
                    primary_local_admin_user_id=local_admin.id,
                    auto_respond_enabled=True,
                    is_active=True,
                    last_synced_at=datetime.now(UTC),
                    **item,
                )
                db.add(profile)
                db.flush()
            created_profiles.append(profile)

        templates_data = [
            (BrandEnum.MARUTI, ReviewSentimentEnum.NEGATIVE, "We are sorry about your experience. Our branch team will contact you shortly."),
            (BrandEnum.KUTTUKARAN, ReviewSentimentEnum.NEGATIVE, "We regret the inconvenience caused. Our team will review this immediately."),
            (BrandEnum.MARUTI, ReviewSentimentEnum.POSITIVE, "Thank you for your review and for choosing Maruti."),
        ]
        for brand, sentiment, template_text in templates_data:
            template = db.scalar(
                select(ReplyTemplate).where(
                    ReplyTemplate.tenant_id == tenant.id,
                    ReplyTemplate.brand == brand,
                    ReplyTemplate.sentiment == sentiment,
                )
            )
            if template is None:
                db.add(
                    ReplyTemplate(
                        tenant_id=tenant.id,
                        brand=brand,
                        sentiment=sentiment,
                        template_text=template_text,
                        updated_by_user_id=user.id,
                    )
                )

        review_specs = [
            (
                created_profiles[0],
                "review-maruti-kochi-001",
                "Akhil",
                5,
                "Very smooth delivery experience and excellent staff support.",
                ReviewSentimentEnum.POSITIVE,
                ReviewStatusEnum.REPLIED,
                "Thank you, Akhil. We are glad the delivery experience felt smooth and well supported.",
            ),
            (
                created_profiles[1],
                "review-kuttukaran-thrissur-001",
                "Nithin",
                2,
                "Service follow-up was delayed and I had trouble getting updates.",
                ReviewSentimentEnum.NEGATIVE,
                ReviewStatusEnum.REPLIED,
                "We regret the inconvenience caused. Our team will review this immediately.",
            ),
            (
                created_profiles[2],
                "review-maruti-tvm-001",
                "Divya",
                4,
                "The service team was helpful and the car was delivered on time.",
                ReviewSentimentEnum.POSITIVE,
                ReviewStatusEnum.PENDING,
                None,
            ),
        ]
        for profile, review_id, reviewer_name, star_rating, text, sentiment, status, reply_text in review_specs:
            review = db.scalar(select(Review).where(Review.gbp_review_id == review_id))
            if review is None:
                review = Review(
                    tenant_id=tenant.id,
                    gbp_profile_id=profile.id,
                    gbp_review_id=review_id,
                    reviewer_name=reviewer_name,
                    star_rating=star_rating,
                    review_text=text,
                    sentiment=sentiment,
                    status=status,
                    review_posted_at=datetime.now(UTC) - timedelta(days=star_rating),
                    last_synced_at=datetime.now(UTC),
                    status_changed_at=datetime.now(UTC),
                    raw_payload_json={"seeded": True},
                )
                db.add(review)
                db.flush()

            if reply_text:
                reply = db.scalar(select(Reply).where(Reply.review_id == review.id))
                if reply is None:
                    db.add(
                        Reply(
                            review_id=review.id,
                            reply_text=reply_text,
                            reply_type=(
                                ReplyTypeEnum.AI_GENERATED
                                if sentiment == ReviewSentimentEnum.POSITIVE
                                else ReplyTypeEnum.TEMPLATED
                            ),
                            posted_to_google=True,
                            posted_at=datetime.now(UTC),
                            created_by_user_id=user.id,
                        )
                    )

            if sentiment == ReviewSentimentEnum.NEGATIVE:
                alert = db.scalar(select(AlertLog).where(AlertLog.review_id == review.id))
                if alert is None:
                    db.add(
                        AlertLog(
                            tenant_id=tenant.id,
                            review_id=review.id,
                            recipient_user_id=local_admin.id,
                            channel=AlertChannelEnum.EMAIL,
                            status=AlertStatusEnum.SENT,
                            sent_at=datetime.now(UTC),
                        )
                    )

        db.commit()
        print(
            "Seeded tenant `kuttukaran`, admin `admin@example.com`, local admin "
            "`branch.manager@example.com`, sample profiles, reviews, templates, and alerts."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

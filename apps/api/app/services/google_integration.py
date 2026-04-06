from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tokens import decrypt_secret
from app.core.tokens import encrypt_secret
from app.models.entities import GoogleAccount
from app.models.entities import Membership
from app.models.entities import OAuthState
from app.models.entities import Reply
from app.models.entities import ReplyTemplate
from app.models.entities import ReplyTypeEnum
from app.models.entities import Review
from app.models.entities import ReviewSentimentEnum
from app.models.entities import ReviewStatusEnum
from app.services.gemini import generate_positive_reply


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GBP_ACCOUNTS_URL = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
GBP_LOCATIONS_URL = "https://mybusinessbusinessinformation.googleapis.com/v1/{parent}/locations"
GBP_REVIEWS_URL = "https://mybusiness.googleapis.com/v4/{parent}/reviews"
GBP_REPLY_URL = "https://mybusiness.googleapis.com/v4/{review_name}/reply"
LOCATION_READ_MASK = ",".join(
    [
        "title",
        "storeCode",
        "websiteUri",
        "phoneNumbers",
        "categories",
        "storefrontAddress",
        "openInfo",
        "metadata",
    ]
)


@dataclass
class SyncResult:
    connected_accounts: int = 0
    synced_locations: int = 0
    synced_reviews: int = 0
    replies_posted: int = 0
    errors: list[str] | None = None

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


def _format_sync_error(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


def ensure_google_oauth_configured() -> None:
    required = [
        settings.google_oauth_client_id,
        settings.google_oauth_client_secret,
        settings.google_oauth_redirect_uri,
        settings.google_token_encryption_key,
    ]
    if not all(required):
        raise ValueError("Google OAuth env vars are not fully configured")


def create_oauth_state(db: Session, membership: Membership) -> str:
    ensure_google_oauth_configured()
    state_token = uuid4().hex
    db.add(
        OAuthState(
            tenant_id=membership.tenant_id,
            state_token=state_token,
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
    )
    db.commit()
    return state_token


def build_google_authorization_url(state_token: str) -> str:
    params = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": settings.google_oauth_redirect_uri,
            "response_type": "code",
            "scope": " ".join(settings.google_oauth_scopes),
            "access_type": "offline",
            "prompt": "consent",
            "state": state_token,
            "include_granted_scopes": "true",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{params}"


async def exchange_code_for_tokens(code: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": settings.google_oauth_redirect_uri,
            },
        )
        response.raise_for_status()
        return response.json()


async def refresh_access_token(refresh_token: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def fetch_gbp_accounts(access_token: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            GBP_ACCOUNTS_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"pageSize": 20},
        )
        response.raise_for_status()
        return response.json().get("accounts", [])


async def fetch_locations(access_token: str, account_name: str) -> list[dict]:
    locations: list[dict] = []
    next_page_token = None
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            params = {
                "readMask": LOCATION_READ_MASK,
                "pageSize": 100,
            }
            if next_page_token:
                params["pageToken"] = next_page_token
            response = await client.get(
                GBP_LOCATIONS_URL.format(parent=account_name),
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
            )
            response.raise_for_status()
            payload = response.json()
            locations.extend(payload.get("locations", []))
            next_page_token = payload.get("nextPageToken")
            if not next_page_token:
                break
    return locations


async def fetch_reviews(access_token: str, location_name: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            GBP_REVIEWS_URL.format(parent=location_name),
            headers={"Authorization": f"Bearer {access_token}"},
            params={"pageSize": 50, "orderBy": "updateTime desc"},
        )
        response.raise_for_status()
        return response.json()


async def post_review_reply(access_token: str, review_name: str, reply_text: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.put(
            GBP_REPLY_URL.format(review_name=review_name),
            headers={"Authorization": f"Bearer {access_token}"},
            json={"comment": reply_text},
        )
        response.raise_for_status()
        return response.json()


async def handle_google_oauth_callback(db: Session, code: str, state: str) -> int:
    oauth_state = db.scalar(select(OAuthState).where(OAuthState.state_token == state))
    if oauth_state is None or oauth_state.expires_at < datetime.now(UTC):
        raise ValueError("OAuth state is invalid or expired")

    tokens = await exchange_code_for_tokens(code)
    refresh_token = tokens.get("refresh_token")
    access_token = tokens.get("access_token")
    if not refresh_token or not access_token:
        raise ValueError("Google OAuth did not return both access and refresh tokens")

    google_accounts = await fetch_gbp_accounts(access_token)
    if not google_accounts:
        raise ValueError("No Google Business Profile accounts were returned")

    encrypted_refresh_token = encrypt_secret(refresh_token)
    connected_count = 0
    for account in google_accounts:
        email = account.get("accountName") or account.get("accountNumber") or account["name"]
        existing_account = db.scalar(
            select(GoogleAccount).where(
                GoogleAccount.tenant_id == oauth_state.tenant_id,
                GoogleAccount.google_account_id == account["name"],
            )
        )
        if existing_account is None:
            existing_account = GoogleAccount(
                tenant_id=oauth_state.tenant_id,
                email=email,
                google_account_id=account["name"],
                encrypted_refresh_token=encrypted_refresh_token,
                scopes_json=settings.google_oauth_scopes,
                is_active=True,
            )
            db.add(existing_account)
        else:
            existing_account.email = email
            existing_account.encrypted_refresh_token = encrypted_refresh_token
            existing_account.scopes_json = settings.google_oauth_scopes
            existing_account.is_active = True

        existing_account.token_last_refreshed_at = datetime.now(UTC)
        connected_count += 1

    db.delete(oauth_state)
    db.commit()
    return connected_count


def _extract_city(location: dict) -> str | None:
    address = location.get("storefrontAddress") or {}
    return address.get("locality")


def _extract_state(location: dict) -> str | None:
    address = location.get("storefrontAddress") or {}
    return address.get("administrativeArea")


def _derive_brand(location: dict) -> str:
    title = (location.get("title") or "").lower()
    if "maruti" in title:
        return "maruti"
    if "kuttukaran" in title:
        return "kuttukaran"
    return "other"


def _extract_rating_value(star_rating: str | None) -> int:
    mapping = {
        "ONE": 1,
        "TWO": 2,
        "THREE": 3,
        "FOUR": 4,
        "FIVE": 5,
    }
    return mapping.get((star_rating or "").upper(), 0)


def _parse_google_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _derive_sentiment(star_rating: int) -> ReviewSentimentEnum:
    return ReviewSentimentEnum.POSITIVE if star_rating >= 4 else ReviewSentimentEnum.NEGATIVE


async def sync_google_account(db: Session, google_account: GoogleAccount) -> SyncResult:
    if not google_account.encrypted_refresh_token or google_account.encrypted_refresh_token == "encrypted-placeholder-token":
        raise ValueError("Google account is a local placeholder and must be replaced by a real OAuth connection")
    refresh_token = decrypt_secret(google_account.encrypted_refresh_token)
    access_token = await refresh_access_token(refresh_token)
    google_account.token_last_refreshed_at = datetime.now(UTC)

    if not google_account.google_account_id:
        accounts = await fetch_gbp_accounts(access_token)
        if not accounts:
            db.commit()
            return SyncResult()
        google_account.google_account_id = accounts[0]["name"]
        google_account.email = (
            accounts[0].get("accountName")
            or accounts[0].get("accountNumber")
            or google_account.email
        )

    result = SyncResult(connected_accounts=1)
    locations = await fetch_locations(access_token, google_account.google_account_id)
    result.synced_locations += len(locations)

    from app.models.entities import BrandEnum
    from app.models.entities import GBPProfile

    for location in locations:
        gbp_location_id = location["name"].split("/")[-1]
        profile = db.scalar(select(GBPProfile).where(GBPProfile.gbp_location_id == gbp_location_id))
        if profile is None:
            profile = GBPProfile(
                tenant_id=google_account.tenant_id,
                google_account_id=google_account.id,
                gbp_location_id=gbp_location_id,
                business_name=location.get("title") or gbp_location_id,
                store_code=location.get("storeCode"),
                city=_extract_city(location),
                state=_extract_state(location),
                brand=BrandEnum(_derive_brand(location)),
                is_active=True,
                auto_respond_enabled=True,
            )
            db.add(profile)
            db.flush()
        else:
            profile.business_name = location.get("title") or profile.business_name
            profile.store_code = location.get("storeCode")
            profile.city = _extract_city(location)
            profile.state = _extract_state(location)
            profile.last_synced_at = datetime.now(UTC)

        reviews_payload = await fetch_reviews(access_token, location["name"])
        review_items = reviews_payload.get("reviews", [])
        payload_ratings = [_extract_rating_value(item.get("starRating")) for item in review_items]
        payload_ratings = [value for value in payload_ratings if value]
        profile.avg_rating_cached = (
            sum(payload_ratings) / len(payload_ratings) if payload_ratings else reviews_payload.get("averageRating") or 0
        )
        profile.total_reviews_cached = reviews_payload.get("totalReviewCount") or len(review_items)
        profile.last_synced_at = datetime.now(UTC)

        for item in review_items:
            review_name = item["reviewId"] if "reviewId" in item else item["name"].split("/")[-1]
            star_rating = _extract_rating_value(item.get("starRating"))
            if not star_rating:
                continue

            review = db.scalar(select(Review).where(Review.gbp_review_id == review_name))
            if review is None:
                review = Review(
                    tenant_id=google_account.tenant_id,
                    gbp_profile_id=profile.id,
                    gbp_review_id=review_name,
                    reviewer_name=(item.get("reviewer") or {}).get("displayName"),
                    star_rating=star_rating,
                    review_text=item.get("comment"),
                    sentiment=_derive_sentiment(star_rating),
                    status=ReviewStatusEnum.PENDING,
                    review_posted_at=_parse_google_timestamp(item.get("createTime")),
                    last_synced_at=datetime.now(UTC),
                    raw_payload_json=item,
                )
                db.add(review)
                db.flush()
                result.synced_reviews += 1
            else:
                review.reviewer_name = (item.get("reviewer") or {}).get("displayName")
                review.star_rating = star_rating
                review.review_text = item.get("comment")
                review.sentiment = _derive_sentiment(star_rating)
                review.review_posted_at = _parse_google_timestamp(item.get("createTime"))
                review.last_synced_at = datetime.now(UTC)
                review.raw_payload_json = item

            if review.status == ReviewStatusEnum.PENDING and profile.auto_respond_enabled:
                reply = db.scalar(select(Reply).where(Reply.review_id == review.id))
                if reply is None:
                    if review.sentiment == ReviewSentimentEnum.POSITIVE:
                        reply_text = await generate_positive_reply(
                            review.review_text,
                            review.reviewer_name,
                            profile.business_name,
                        )
                        reply_type = ReplyTypeEnum.AI_GENERATED
                    else:
                        template = db.scalar(
                            select(ReplyTemplate).where(
                                ReplyTemplate.tenant_id == google_account.tenant_id,
                                ReplyTemplate.brand == profile.brand,
                                ReplyTemplate.sentiment == ReviewSentimentEnum.NEGATIVE,
                                ReplyTemplate.is_active.is_(True),
                            )
                        )
                        if template is None:
                            reply_text = (
                                "We are sorry about your experience. Our team will review your feedback and reach out."
                            )
                        else:
                            reply_text = template.template_text
                        reply_type = ReplyTypeEnum.TEMPLATED

                    await post_review_reply(access_token, item["name"], reply_text)
                    db.add(
                        Reply(
                            review_id=review.id,
                            reply_text=reply_text,
                            reply_type=reply_type,
                            generation_model=settings.gemini_model if reply_type == ReplyTypeEnum.AI_GENERATED else None,
                            posted_to_google=True,
                            posted_at=datetime.now(UTC),
                        )
                    )
                    review.status = ReviewStatusEnum.REPLIED
                    review.status_changed_at = datetime.now(UTC)
                    result.replies_posted += 1

    db.commit()
    return result


async def sync_all_google_accounts(db: Session, tenant_id) -> SyncResult:
    accounts = db.scalars(
        select(GoogleAccount).where(
            GoogleAccount.tenant_id == tenant_id,
            GoogleAccount.is_active.is_(True),
        )
    ).all()
    aggregate = SyncResult()
    for google_account in accounts:
        try:
            result = await sync_google_account(db, google_account)
            aggregate.connected_accounts += result.connected_accounts
            aggregate.synced_locations += result.synced_locations
            aggregate.synced_reviews += result.synced_reviews
            aggregate.replies_posted += result.replies_posted
            aggregate.errors.extend(result.errors or [])
        except Exception as exc:
            db.rollback()
            aggregate.errors.append(f"{google_account.email}: {_format_sync_error(exc)}")
    return aggregate

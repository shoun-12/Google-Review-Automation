# ERD And Domain Model

## Scope

This document defines the initial database design for the Google Review Automation dashboard. It is derived from `Agents.md` and adapted from the draft in `models.md` for a FastAPI/PostgreSQL implementation.

## Design Principles

- Every business record is tenant-scoped
- External integrations must be idempotent and auditable
- Review ingestion and reply posting must preserve history
- v1 supports `master_admin` and `local_admin`, but the schema should allow future role expansion
- Soft delete is used for selected operational entities where audit history matters

## Core Entities

### 1. tenants

Represents a customer/business group. V1 may run with one tenant, but the schema remains multi-tenant-ready.

Key columns:
- `id` UUID PK
- `name`
- `slug`
- `website_domain` nullable
- `is_active`
- `created_at`
- `updated_at`
- `deleted_at` nullable

### 2. users

Internal dashboard users.

Key columns:
- `id` UUID PK
- `email` unique
- `password_hash`
- `full_name`
- `phone_number` nullable
- `avatar_url` nullable
- `is_platform_admin` default false
- `is_active`
- `last_login_at` nullable
- `created_at`
- `updated_at`

Notes:
- Prefer custom auth table instead of framework-default user abstraction leaking into domain design.

### 3. memberships

Maps users to tenants and defines role within a tenant.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `user_id` FK -> users
- `role` enum: `master_admin`, `local_admin`
- `email_alerts_enabled`
- `whatsapp_alerts_enabled`
- `is_active`
- `joined_at`
- `invited_by_user_id` nullable FK -> users

Constraints:
- unique `(tenant_id, user_id)`

### 4. oauth_states

Temporary state records used during Google OAuth flows.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `state_token` unique
- `expires_at`
- `created_at`

### 5. google_accounts

Connected Google accounts with Business Profile access.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `email`
- `google_account_id` nullable
- `encrypted_refresh_token`
- `token_last_refreshed_at` nullable
- `scopes_json`
- `is_active`
- `connected_by_user_id` nullable FK -> users
- `created_at`
- `updated_at`

Constraints:
- unique `(tenant_id, email)`

Notes:
- Refresh tokens must be encrypted at rest.
- Access tokens should not be permanently stored unless operationally necessary.

### 6. gbp_profiles

Represents individual business locations pulled from Google Business Profile.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `google_account_id` FK -> google_accounts
- `primary_local_admin_user_id` nullable FK -> users
- `gbp_location_id` unique
- `business_name`
- `store_code` nullable
- `city` nullable
- `state` nullable
- `brand` enum: `kuttukaran`, `maruti`, `other`
- `avg_rating_cached`
- `total_reviews_cached`
- `last_review_activity_at` nullable
- `auto_respond_enabled`
- `is_active`
- `last_synced_at` nullable
- `created_at`
- `updated_at`
- `deleted_at` nullable

Indexes:
- `(tenant_id, brand)`
- `(tenant_id, is_active)`
- `(tenant_id, city)`

### 7. profile_assignments

Optional many-to-many assignment table for local-admin access control and future flexibility.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `user_id` FK -> users
- `gbp_profile_id` FK -> gbp_profiles
- `is_active`
- `assigned_at`
- `assigned_by_user_id` nullable FK -> users

Constraints:
- unique active assignment per `(user_id, gbp_profile_id)`

Notes:
- Keep this even if a primary local admin field exists on `gbp_profiles`.

### 8. reviews

Stores synchronized Google reviews.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `gbp_profile_id` FK -> gbp_profiles
- `gbp_review_id` unique
- `reviewer_name` nullable
- `star_rating`
- `review_text`
- `sentiment` enum: `positive`, `negative`, `neutral`
- `status` enum: `pending`, `replied`, `ignored`, `failed`
- `review_posted_at`
- `last_synced_at`
- `status_changed_at` nullable
- `raw_payload_json`
- `created_at`
- `deleted_at` nullable

Indexes:
- `(gbp_profile_id, review_posted_at)`
- `(gbp_profile_id, status)`
- `(tenant_id, sentiment)`
- `(tenant_id, review_posted_at)`

Rules:
- `4-5` stars => `positive`
- `1-3` stars => `negative`

### 9. reply_templates

Stores approved brand/sentiment reply templates.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `brand` enum
- `sentiment` enum
- `template_text`
- `is_active`
- `updated_by_user_id` nullable FK -> users
- `created_at`
- `updated_at`

Constraints:
- unique `(tenant_id, brand, sentiment)`

Notes:
- Negative review templates are required in v1.
- Positive templates may still exist as fallback if AI generation is disabled.

### 10. replies

Stores the reply chosen/generated for a review and tracks posting state.

Key columns:
- `id` UUID PK
- `review_id` unique FK -> reviews
- `reply_text`
- `reply_type` enum: `ai_generated`, `templated`, `manual`
- `generation_model` nullable
- `posted_to_google`
- `posted_at` nullable
- `created_by_user_id` nullable FK -> users
- `created_at`

Notes:
- For automated replies, `created_by_user_id` may be null and the action should be captured in audit logs.

### 11. alert_logs

Tracks negative review notifications and delivery outcomes.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `review_id` FK -> reviews
- `recipient_user_id` nullable FK -> users
- `channel` enum: `email`, `whatsapp`
- `status` enum: `queued`, `sent`, `failed`
- `provider_message_id` nullable
- `failure_reason` nullable
- `sent_at` nullable
- `created_at`

Indexes:
- `(tenant_id, channel, status)`
- `(review_id, channel)`

### 12. audit_logs

Append-only record of important user and system actions.

Key columns:
- `id` UUID PK
- `tenant_id` nullable FK -> tenants
- `actor_user_id` nullable FK -> users
- `target_type`
- `target_id` nullable
- `action`
- `metadata_json`
- `created_at`

Indexes:
- `(tenant_id, created_at)`
- `(action, created_at)`

Examples:
- user created
- user suspended
- google account connected
- locations synced
- review reply posted
- alert failed

### 13. analytics_daily_snapshots

Optional pre-aggregated metrics table for later optimization.

Key columns:
- `id` UUID PK
- `tenant_id` FK -> tenants
- `gbp_profile_id` nullable FK -> gbp_profiles
- `snapshot_date`
- `reviews_received`
- `positive_reviews`
- `negative_reviews`
- `replies_posted`
- `alerts_sent`
- `avg_rating`
- `created_at`

Constraints:
- unique `(tenant_id, gbp_profile_id, snapshot_date)`

Notes:
- Not required for initial implementation if live queries are fast enough.

## Relationship Summary

```text
tenants 1---* memberships *---1 users
tenants 1---* google_accounts
tenants 1---* gbp_profiles
users 1---* profile_assignments *---1 gbp_profiles
google_accounts 1---* gbp_profiles
gbp_profiles 1---* reviews
reviews 1---0..1 replies
reviews 1---* alert_logs
tenants 1---* reply_templates
tenants 1---* audit_logs
```

## Authorization Mapping

### master_admin

- Full tenant-wide access
- Can manage users, assignments, settings, templates, logs, and reports
- Can connect/disconnect Google accounts

### local_admin

- Can access only assigned profiles
- Can view related reviews, alerts, and profile activity
- Can manage own notification preferences

## Soft Delete Policy

Use `deleted_at` for:
- tenants
- gbp_profiles
- reviews

Do not soft-delete:
- replies
- alert_logs
- audit_logs

Reason:
- Operational entities may need restoration or exclusion from default views.
- Historical action tables should remain append-only.

## Open Decisions

- Whether to store Google account subject ID separately from email for resilience against email changes
- Whether to support multiple local admins per profile in v1 UI or only in the schema
- Whether exports should be synchronous at first or queued immediately
- Whether to add a dedicated `notification_preferences` table later if preferences become per-profile rather than per-membership

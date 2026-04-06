# API Specification

## Scope

This document defines the initial REST API surface for the dashboard. It is intentionally focused on v1 capabilities and should be implemented behind role-based access control.

Base path:

```text
/api/v1
```

## Conventions

- JSON request/response bodies
- JWT bearer access token for authenticated endpoints
- Pagination via `page` and `page_size`
- Timestamps in ISO 8601 UTC
- Errors returned in a consistent envelope

Example error:

```json
{
  "error": {
    "code": "forbidden",
    "message": "You do not have access to this resource."
  }
}
```

## Auth

### POST `/auth/login`

Authenticate dashboard user.

Request:

```json
{
  "email": "admin@example.com",
  "password": "secret"
}
```

Response:

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "email": "admin@example.com",
    "full_name": "Master Admin"
  }
}
```

### POST `/auth/refresh`

Rotate refresh token and issue new access token.

### POST `/auth/logout`

Invalidate refresh token/session.

### GET `/auth/me`

Return current user, tenant membership, and effective permissions.

## Users And Memberships

### GET `/users`

Master Admin only. List tenant users.

Filters:
- `role`
- `is_active`
- `search`

### POST `/users`

Master Admin only. Create Local Admin or additional Master Admin.

Request:

```json
{
  "email": "branch.manager@example.com",
  "full_name": "Branch Manager",
  "phone_number": "+91XXXXXXXXXX",
  "role": "local_admin",
  "email_alerts_enabled": true,
  "whatsapp_alerts_enabled": true
}
```

### GET `/users/{user_id}`

Master Admin only.

### PATCH `/users/{user_id}`

Master Admin only. Update profile fields, alert preferences, or role.

### POST `/users/{user_id}/suspend`

Master Admin only.

### POST `/users/{user_id}/reactivate`

Master Admin only.

### DELETE `/users/{user_id}`

Master Admin only. Soft-delete or disable depending on implementation choice.

## Google Account Integration

### POST `/google/oauth/start`

Master Admin only. Begin OAuth flow.

Response:

```json
{
  "authorization_url": "https://accounts.google.com/..."
}
```

### GET `/google/oauth/callback`

OAuth callback endpoint used by Google. Exchanges code and stores credentials.

### GET `/google/accounts`

Master Admin only. List connected Google accounts.

### POST `/google/accounts/{account_id}/sync-locations`

Master Admin only. Queue location sync.

### POST `/google/accounts/{account_id}/disconnect`

Master Admin only. Disable account and stop future sync jobs.

## Profiles

### GET `/profiles`

List GBP profiles visible to current user.

Filters:
- `search`
- `brand`
- `city`
- `is_active`
- `local_admin_user_id`
- `auto_respond_enabled`

Response fields:
- `id`
- `business_name`
- `city`
- `brand`
- `avg_rating_cached`
- `total_reviews_cached`
- `primary_local_admin`
- `last_review_activity_at`
- `is_active`
- `auto_respond_enabled`

### GET `/profiles/{profile_id}`

Detailed profile view.

### PATCH `/profiles/{profile_id}`

Master Admin only. Update profile settings such as `auto_respond_enabled`, `is_active`, or assignment.

### GET `/profiles/{profile_id}/reviews`

List reviews for one profile.

Filters:
- `sentiment`
- `status`
- `date_from`
- `date_to`

### POST `/profiles/{profile_id}/assignments`

Master Admin only. Assign Local Admin to profile.

Request:

```json
{
  "user_id": "uuid"
}
```

### DELETE `/profiles/{profile_id}/assignments/{assignment_id}`

Master Admin only. Remove assignment.

## Reviews

### GET `/reviews`

Tenant-wide review feed for Master Admin; assignment-scoped feed for Local Admin.

Filters:
- `profile_id`
- `sentiment`
- `status`
- `date_from`
- `date_to`
- `search`

### GET `/reviews/{review_id}`

Return review details, reply data, and alert history.

### POST `/reviews/{review_id}/reply`

Master Admin only for v1 manual overrides.

Request:

```json
{
  "reply_text": "Thank you for your feedback.",
  "reply_type": "manual",
  "post_to_google": true
}
```

### POST `/reviews/{review_id}/retry-automation`

Master Admin only. Re-queue failed automation.

## Reply Templates

### GET `/reply-templates`

Master Admin only.

Filters:
- `brand`
- `sentiment`
- `is_active`

### POST `/reply-templates`

Master Admin only.

Request:

```json
{
  "brand": "maruti",
  "sentiment": "negative",
  "template_text": "We are sorry to hear about your experience."
}
```

### PATCH `/reply-templates/{template_id}`

Master Admin only.

### DELETE `/reply-templates/{template_id}`

Master Admin only or convert to inactive if soft-retention is preferred.

## Notifications

### GET `/notifications/alerts`

Master Admin sees tenant-wide alerts. Local Admin sees own alerts only.

Filters:
- `channel`
- `status`
- `date_from`
- `date_to`

### GET `/notifications/preferences/me`

Return current user notification settings.

### PATCH `/notifications/preferences/me`

Local Admin or Master Admin. Update own alert preferences.

Request:

```json
{
  "email_alerts_enabled": true,
  "whatsapp_alerts_enabled": false
}
```

## Reports

### GET `/reports/summary`

Master Admin only.

Query params:
- `date_from`
- `date_to`

Response:

```json
{
  "total_connected_profiles": 75,
  "reviews_received": 132,
  "positive_reviews": 102,
  "negative_reviews": 30,
  "ai_response_rate": 0.91,
  "alert_delivery_rate": 0.96,
  "average_rating_network": 4.32
}
```

### GET `/reports/ratings-by-profile`

Master Admin only. Returns profile-level rating and review aggregates.

### GET `/reports/reviews-trend`

Master Admin only. Returns time-series counts by date range.

### POST `/reports/export/csv`

Master Admin only. Generate CSV export for a selected report.

Request:

```json
{
  "report_type": "reviews",
  "date_from": "2026-01-01T00:00:00Z",
  "date_to": "2026-01-31T23:59:59Z"
}
```

Response:

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

## Audit Logs

### GET `/audit-logs`

Master Admin only.

Filters:
- `action`
- `actor_user_id`
- `date_from`
- `date_to`
- `target_type`

## Internal / Worker Endpoints

These should not be exposed publicly without service authentication.

### POST `/internal/sync/google-account/{account_id}`

Trigger or retry location/review sync.

### POST `/internal/reviews/{review_id}/process`

Run review automation pipeline.

### POST `/internal/reports/{job_id}/run`

Run export job.

## Initial Permission Matrix

### Master Admin

- Full access to all endpoints

### Local Admin

- `GET /auth/me`
- `GET /profiles`
- `GET /profiles/{id}`
- `GET /profiles/{id}/reviews`
- `GET /reviews`
- `GET /reviews/{id}`
- `GET /notifications/alerts`
- `GET /notifications/preferences/me`
- `PATCH /notifications/preferences/me`

Notes:
- Local Admin access must always be constrained to assigned profiles and self-owned notification preferences.

## Deferred API Areas

- Password reset flow
- Invitation acceptance flow
- Bulk profile assignment
- PDF exports
- Manual reconnect flow for expired Google credentials
- Webhooks from notification providers if delivery receipts are required later

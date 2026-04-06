# Implementation Status

This document is a working reference for the current state of the Google Review Automation project.

It is meant to answer two questions quickly:

1. What has already been implemented?
2. What should be implemented next?

## Product Scope

The application is an internal dashboard for managing Google Business Profiles across multiple Google accounts for Kuttukaran and Maruti.

Current product direction:

- private internal web app
- multi-tenant-ready backend structure
- two main roles in active use:
  - `master_admin`
  - `local_admin`
- Google OAuth based account connection
- review sync and reply automation
- reporting and operational visibility

## Implemented Features

### Backend Foundation

- FastAPI application with versioned API routing
- SQLAlchemy ORM models
- Alembic initial migration
- PostgreSQL session setup
- Redis and Celery scaffolding
- Docker Compose local environment

### Authentication And Access Control

- internal login with email and password
- JWT access tokens
- refresh token persistence in database
- active-user validation
- tenant membership model
- role checks for `master_admin` and `local_admin`
- protected frontend routes

### Multi-Tenant Data Model

- tenants
- users
- memberships
- refresh tokens
- Google OAuth state
- Google accounts
- GBP profiles
- reviews
- replies
- reply templates
- audit logs
- profile assignment model scaffold

### Google Integration

- Google OAuth start endpoint
- Google OAuth callback handling
- secure Google refresh token encryption at rest
- Google account storage per tenant
- support for more than one connected Google account
- manual sync endpoint for Google Business Profile data

### Sync And Automation

- location fetch and storage as GBP profiles
- review fetch and storage
- positive review detection
- negative review detection
- AI-generated positive reply flow
- fallback positive reply when Gemini key is missing
- templated negative reply flow
- reply posting back to Google
- Celery task entrypoints for sync

### Dashboard And UI

- login page
- protected app shell
- collapsible sidebar navigation
- icon-based sidebar collapsed state
- responsive shell layout
- dashboard metrics cards
- dashboard review trend graph
- dashboard sentiment panel
- dashboard branch performance panel
- local-admin scoped analytics on the dashboard
- profiles page
- reviews page
- users page
- settings page
- audit logs page

### Reporting

- summary metrics
- trend data for recent review activity
- profile performance aggregation
- CSV export for profile performance

### Admin Operations

- create internal users
- update users
- suspend/reactivate through `is_active`
- assign a primary local admin to a profile
- toggle profile auto-response
- view Google account inventory
- create and update reply templates

### Auditability

- audit log writes for major actions such as:
  - profile update
  - user create/update
  - Google OAuth start
  - Google sync trigger
- audit log page in the frontend
- audit metadata now shown in UI-friendly form instead of raw JSON blocks

## Partially Implemented Features

These areas exist in some form, but are not yet fully complete.

### Local Admin Assignment Model

- `primary_local_admin_user_id` is actively used
- `ProfileAssignment` model exists
- many-to-many profile assignment workflow is not fully wired into access control and UI

### Refresh Token Lifecycle

- refresh tokens are issued and persisted
- frontend session persistence exists
- automatic token refresh flow is not fully wired into the frontend API client

### Scheduled Sync

- worker and beat services exist
- task entrypoints exist
- intended recurring sync behavior is present conceptually
- full production-grade periodic scheduling and monitoring still need tightening

### Analytics

- dashboard analytics and graphs exist
- role-based scoping works for local admins
- date-range flexibility is still limited
- more advanced business insights are not yet implemented

## Not Yet Implemented

These are important product capabilities that are still missing or incomplete compared to the intended scope.

### Notifications And Escalation

- email alerts for negative reviews
- WhatsApp alerts for negative reviews
- alert template management
- alert delivery execution
- alert retry flow
- delivery status visibility end-to-end

### Full Assignment Workflow

- assign one or more profiles to local admins in a dedicated workflow
- manage assignments in a clear UI
- use assignment table consistently for authorization and routing

### Advanced Review Operations

- manual override workflow for generated replies
- review approval workflow
- stronger filtering and searching for reviews
- richer branch-level review ownership workflow

### Reporting Enhancements

- custom date range filters
- 7/30/90/custom selector in UI
- response-time metrics
- rating distribution
- top and underperforming branch insights
- side-by-side branch comparison
- PDF export

### Admin Lifecycle

- delete user flow with confirmation
- deeper account management UX
- richer profile assignment UX

## Recommended Next Features

These are the features I recommend implementing next, in priority order.

### 1. Negative Review Escalation Pipeline

Why:

- this is one of the core business requirements
- it is the biggest gap between current code and intended product behavior

Suggested scope:

- send email alerts
- send WhatsApp alerts
- respect user alert preferences
- log delivery attempts and final status
- show alert status in dashboard or audit views

### 2. Proper Profile Assignment System

Why:

- local-admin ownership is central to the business workflow
- current scoping relies mainly on one primary-assignee field

Suggested scope:

- implement assignment UI
- support assigning multiple profiles to a local admin
- optionally support multiple admins per profile later
- use the assignment model consistently in API scoping

### 3. Frontend Token Refresh Flow

Why:

- current login persistence is good, but session continuity can be more reliable
- this is important for real internal usage

Suggested scope:

- automatically refresh access tokens
- retry expired requests once after refresh
- clear session cleanly if refresh fails

### 4. Advanced Review Management

Why:

- operational users will need more than sync plus basic listing

Suggested scope:

- filters by status, sentiment, branch, and date
- search by reviewer or branch
- manual reply override and re-post flow
- better visibility into whether a reply was AI, template, or manual

### 5. Richer Reports

Why:

- leadership users will likely ask for better reporting quickly

Suggested scope:

- date range controls in UI
- branch ranking improvements
- sentiment trend summary
- response-rate trend summary
- CSV improvements first, PDF later

### 6. Background Job Hardening

Why:

- sync is a core workflow and should be resilient

Suggested scope:

- periodic sync configuration review
- retries and failure visibility
- operational health checks around worker activity

## Suggested Medium-Term Improvements

- icon system cleanup and shared UI tokens
- reusable table filtering and pagination
- better empty states across all pages
- more structured audit views
- stronger environment validation for required secrets
- automated tests for auth, sync, and reporting flows
- end-to-end test coverage for role-based access

## Practical Current-State Summary

Today, the project already supports:

- internal authentication
- role-aware access
- Google account connection
- GBP sync
- automated replies
- dashboard analytics
- reporting basics
- user management basics
- template management
- audit logging

The main missing capabilities for production readiness are:

- negative review alerting
- full local-admin assignment flow
- session refresh hardening
- deeper review operations
- richer analytics and exports

## Suggested Usage

Use this file as the quick project snapshot before making roadmap decisions, doing handover, or comparing product expectations against the current implementation.

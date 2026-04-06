# Delivery Plan

## Objective

Deliver a production-structured internal dashboard for Google Business Profile management, starting from an empty repository. The first goal is a stable operational system for Kuttukaran and Maruti, not a broad SaaS launch.

## Delivery Strategy

Build the platform in vertical slices, but do not start with UI polish. The critical path is:

1. project foundation
2. auth and authorization
3. Google account connection
4. location sync
5. review polling
6. automation and alerts
7. reporting and operational hardening

## Phase 0: Planning And Setup

### Outcomes

- Architecture and domain docs approved
- Repo structure agreed
- Local development workflow defined
- Environments and secrets documented

### Deliverables

- `docs/architecture.md`
- `docs/erd.md`
- `docs/api-spec.md`
- `docs/delivery-plan.md`
- Initial monorepo folder layout
- Docker Compose skeleton

### Exit Criteria

- Team agrees on stack, service boundaries, and schema direction

## Phase 1: Platform Foundation

### Scope

- Create frontend and backend apps
- Add linting, formatting, testing setup
- Add Docker Compose for local development
- Add environment variable management
- Add CI for lint/test/build checks
- Add Alembic migration framework

### Deliverables

- `apps/web`
- `apps/api`
- `infra/compose`
- base database migration
- CI pipeline

### Exit Criteria

- Fresh clone can run the full stack locally
- Base health endpoints and DB connectivity work

## Phase 2: Identity And Access

### Scope

- Implement internal user auth
- JWT access/refresh flows
- Tenant memberships and role enforcement
- Seed initial Master Admin
- User management endpoints for Master Admin

### Deliverables

- auth models and migrations
- login/logout/refresh endpoints
- current-user endpoint
- RBAC policy layer
- user management APIs

### Exit Criteria

- Master Admin can log in and manage Local Admin accounts
- Local Admin is restricted to assigned data

## Phase 3: Google Integration Foundation

### Scope

- Implement Google OAuth start/callback
- Store encrypted refresh tokens
- Support multiple Google accounts per tenant
- Add token refresh service
- Add audit logging for account connection events

### Deliverables

- google account tables and migrations
- OAuth endpoints
- encryption utility for credentials
- initial Google service client

### Exit Criteria

- Master Admin can connect at least one Google account and persist credentials safely

## Phase 4: Location Synchronization

### Scope

- Fetch GBP locations from connected accounts
- Normalize and store location data
- Build manual sync trigger
- Build profile list API and dashboard-ready fields
- Add profile assignment support

### Deliverables

- location sync worker
- profile persistence layer
- profile list/detail endpoints
- assignment endpoints

### Exit Criteria

- Connected locations appear in dashboard data with assignment capability

## Phase 5: Review Ingestion

### Scope

- Scheduled polling every 15 minutes
- Review de-duplication and updates
- Review persistence and sentiment bucketing
- Cached metrics updates on profiles
- Review feed endpoints

### Deliverables

- Celery beat schedule
- review sync job
- review processing service
- review feed/detail APIs

### Exit Criteria

- New reviews are ingested reliably and visible in dashboard queries

## Phase 6: Reply Automation

### Scope

- Positive review AI reply generation
- Negative review templated apology flow
- GBP reply posting
- Reply history persistence
- Master Admin override endpoint

### Deliverables

- reply template module
- AI reply generator integration
- reply posting service
- retry handling for failed automation

### Exit Criteria

- Positive and negative review automation both execute with audit trails

## Phase 7: Notifications And Escalation

### Scope

- Email alerts for negative reviews
- WhatsApp alerts for negative reviews
- Per-user alert preference controls
- Delivery logging and retries

### Deliverables

- email provider integration
- Twilio WhatsApp integration
- alert queue workers
- notification preference endpoints
- alert log queries

### Exit Criteria

- Assigned Local Admin receives and can control alerts

## Phase 8: Dashboard UI

### Scope

- Login flow
- Profile overview page
- Review feed and detail views
- User and assignment management screens
- Reply template settings
- Notification log views
- Audit log view

### Deliverables

- core route structure
- authenticated layout
- master admin screens
- local admin screens

### Exit Criteria

- Users can operate the platform end-to-end through the UI without relying on raw API calls

## Phase 9: Reporting And Export

### Scope

- Summary metrics
- Date-range filters
- Ratings and review trends
- CSV export

### Deliverables

- reporting queries/services
- report endpoints
- CSV export job
- analytics UI

### Exit Criteria

- Master Admin can download operational reports from the dashboard

## Phase 10: Hardening And Production Readiness

### Scope

- Structured logging
- Error monitoring
- Rate-limit and retry tuning
- Permission audits
- Seed/template strategy
- Deployment configuration
- Backup and restore process

### Deliverables

- production env docs
- monitoring hooks
- runbooks for sync failures and provider outages
- release checklist

### Exit Criteria

- System is ready for controlled production rollout

## Milestone Order

1. Foundation
2. Auth and RBAC
3. Google OAuth
4. Location sync
5. Review ingestion
6. Reply automation
7. Notifications
8. Dashboard UI
9. Reporting
10. Hardening

## Suggested Sprint Plan

### Sprint 1

- Repo scaffolding
- Docker Compose
- FastAPI base app
- React base app
- Postgres and Redis wiring
- Auth schema draft

### Sprint 2

- JWT auth
- RBAC
- user management APIs
- seed admin setup

### Sprint 3

- Google OAuth flow
- encrypted token storage
- connected accounts UI/API

### Sprint 4

- location sync
- profile overview APIs
- profile assignment APIs

### Sprint 5

- review polling
- review feed APIs
- cached metrics updates

### Sprint 6

- AI positive replies
- negative review templates
- reply posting to GBP
- audit events

### Sprint 7

- email and WhatsApp alerts
- alert preferences
- alert logs

### Sprint 8

- admin dashboard pages
- local admin pages
- end-to-end flow cleanup

### Sprint 9

- reports
- CSV export
- query optimization

### Sprint 10

- production hardening
- deployment scripts
- operational runbooks

## Workstream Split

### Backend

- schema and migrations
- auth
- Google integration
- worker jobs
- reporting

### Frontend

- auth UI
- admin dashboard
- local admin dashboard
- reporting UI

### DevOps

- docker setup
- CI/CD
- secrets and config
- deployment

## Risks And Mitigations

### Google API uncertainty

Mitigation:
- validate required scopes and endpoints in an isolated integration spike before full implementation

### Automation misfires

Mitigation:
- keep idempotency keys, audit logs, retry policies, and manual override paths

### Notification failures

Mitigation:
- persist delivery attempts and expose failures in dashboard logs

### Scope creep into generic SaaS

Mitigation:
- keep v1 optimized for internal Kuttukaran/Maruti workflows while preserving tenant boundaries in the schema

## Immediate Next Steps

1. Scaffold the monorepo and local development stack
2. Create the FastAPI service with migrations and auth foundation
3. Create the React app with route shell and auth screens
4. Implement the first migrations from `docs/erd.md`

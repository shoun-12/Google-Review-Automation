# Architecture

## Goal

Build an internal dashboard that consolidates Google Business Profile management for Kuttukaran and Maruti across multiple Google accounts. The system must support review synchronization, automated replies, escalation for negative reviews, auditability, and reporting.

## Guiding Principles

- API-first backend with a separate web client
- Multi-tenant-ready domain model, even though v1 serves one internal business group
- Background-job-driven integration work for polling, notifications, and retries
- Secure storage of external credentials and internal auth tokens
- Full auditability for sensitive actions
- Simple local development with Docker Compose

## High-Level System

### Components

1. Web App
- React + TypeScript + Vite
- TailwindCSS for UI
- React Router for route handling
- TanStack Query for server state

2. API Service
- FastAPI
- SQLAlchemy 2 ORM
- Alembic migrations
- JWT-based auth for dashboard users
- Integration layer for Google Business Profile, email, WhatsApp, and AI reply generation

3. Worker Service
- Celery workers
- Redis-backed queue
- Handles review polling, token refresh jobs, auto-replies, notifications, retries, and reporting jobs

4. Database
- PostgreSQL
- Primary system of record for users, assignments, OAuth credentials, profiles, reviews, replies, notifications, and audit logs

5. Cache / Queue
- Redis
- Celery broker/result backend
- Optional short-lived cache for expensive dashboard queries later

## Deployment Topology

### Local Development

- `web`: React frontend
- `api`: FastAPI app
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `postgres`: PostgreSQL database
- `redis`: Redis broker/cache

### Production

- Frontend hosted as static assets or behind a web server/CDN
- API service behind HTTPS reverse proxy
- Worker and scheduler as separate long-running processes
- Managed PostgreSQL and Redis preferred
- Secret management handled outside source control

## Core Flows

### 1. Internal Authentication

1. User logs into dashboard with email and password
2. API verifies credentials and account status
3. API issues short-lived access token and refresh token
4. Frontend uses access token for authenticated requests
5. Refresh token rotation is used to reduce token theft risk

### 2. Google Account Connection

1. Master Admin initiates Google OAuth
2. API creates state record and redirects user to Google consent screen
3. Google returns authorization code
4. API exchanges code for tokens
5. Refresh token is encrypted before storage
6. Connected Google account is linked to tenant
7. Initial location sync job is queued

### 3. Location Sync

1. Worker fetches locations for each connected Google account
2. Profiles are created or updated in `gbp_profiles`
3. Cached profile metadata is stored for dashboard use
4. Sync results are logged in audit records

### 4. Review Polling and Processing

1. Scheduler triggers sync every 15 minutes per active Google account
2. Worker refreshes access token if needed
3. Worker fetches reviews from GBP APIs
4. New or updated reviews are stored
5. Review sentiment bucket is derived from star rating
6. Follow-up jobs are queued for reply handling and alerting

### 5. Positive Review Automation

1. New 4-5 star review is detected
2. Worker sends review context to AI reply generator
3. Generated draft is stored
4. Reply is posted through GBP API
5. Review status, reply record, and audit log are updated

### 6. Negative Review Escalation

1. New 1-3 star review is detected
2. Worker selects active brand-level apology template
3. Reply is posted through GBP API
4. Assigned Local Admin is identified
5. Email and WhatsApp alerts are queued based on notification preferences
6. Delivery results are persisted to alert logs

## Service Boundaries

### Frontend Responsibilities

- Authentication screens and session handling
- Profile and review dashboards
- Assignment and user management UI
- Template and notification settings UI
- Analytics and export UI

### API Responsibilities

- Auth and authorization
- Domain CRUD and dashboard queries
- External integration orchestration
- Validation and business rules
- Audit logging

### Worker Responsibilities

- Scheduled polling
- Token refresh and retry handling
- AI reply generation
- GBP reply posting
- Email and WhatsApp delivery
- Report/export job execution when needed

## Security Model

### Internal Users

- Dashboard is private, not public
- Passwords stored using a modern password hash
- JWT access tokens short-lived
- Refresh tokens rotated and revocable
- Suspended users denied at auth and authorization layers

### Google Credentials

- Refresh tokens encrypted at rest
- Encryption key stored in environment secret manager
- Token access limited to integration services
- Full audit logging for connect/disconnect/reconnect events

### Authorization

- `master_admin`: full tenant access
- `local_admin`: only assigned profiles and related reviews/alerts
- Policy checks enforced in API layer, not just UI

## Data Ownership

### Tenant Strategy

Even if v1 serves one operating group, all business data should be tenant-scoped so the platform can support additional customers later.

### Profile Assignment

- Each GBP profile belongs to one tenant
- A profile may have a primary local admin reference for accountability
- Assignment table supports many-to-many relationships if needed later

## Observability

- Structured logs in API and worker services
- Audit logs for user and system actions
- Health endpoints for API, worker, database, and Redis connectivity
- Error tracking integration recommended before production rollout

## Non-Goals for V1

- Public customer portal
- Native mobile app
- Advanced analytics warehouse
- Full PDF reporting
- Complex workflow engine for manual review approvals

## Recommended Repo Structure

```text
.
├── apps/
│   ├── api/
│   └── web/
├── docs/
│   ├── architecture.md
│   ├── erd.md
│   ├── api-spec.md
│   └── delivery-plan.md
├── infra/
│   ├── docker/
│   └── compose/
└── scripts/
```

## Initial Technical Decisions

- Backend framework: FastAPI
- ORM: SQLAlchemy 2
- Migrations: Alembic
- Worker queue: Celery
- Broker/cache: Redis
- Frontend build: Vite
- UI styling: TailwindCSS
- Charts: Recharts
- Email provider: Resend
- WhatsApp provider: Twilio
- Database: PostgreSQL

## Risks to Address Early

- Google Business Profile API scope and endpoint constraints
- Token refresh reliability across multiple connected accounts
- Rate limiting and retry policy for GBP API calls
- Duplicate review ingestion and idempotent processing
- Safe AI reply generation with consistent brand tone
- Notification delivery failures and escalation visibility

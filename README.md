# Google Review Automation

Internal dashboard for managing Google Business Profiles, automated review replies, local-admin escalation, and reporting for Kuttukaran and Maruti.

## Repo Structure

```text
.
├── apps/
│   ├── api/
│   └── web/
├── docs/
├── infra/
└── scripts/
```

## Current State

This repository is scaffolded for:

- FastAPI backend
- React + Vite frontend
- PostgreSQL
- Redis
- Celery worker and scheduler
- Docker Compose local development

## Bootstrap Notes

Environment defaults have been copied to `.env`.

Useful local commands:

```bash
make api-compile
make api-bootstrap
make api-seed
make api-generate-key
```

Seed defaults:

```text
email: admin@example.com
password: ChangeMe123!
tenant: kuttukaran
```

Required env vars for live integration:

```text
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_REDIRECT_URI
GOOGLE_TOKEN_ENCRYPTION_KEY
GEMINI_API_KEY
```

`GOOGLE_TOKEN_ENCRYPTION_KEY` must be a Fernet key. You can generate one with:

```bash
make api-generate-key
```

## Planned Startup

Once dependencies are installed, the intended local flow is:

```bash
docker compose up --build
```

Frontend:

```text
http://localhost:3000
```

API:

```text
http://localhost:8000
```

## Planning Docs

- `docs/architecture.md`
- `docs/erd.md`
- `docs/api-spec.md`
- `docs/delivery-plan.md`

## Current Backend Progress

- SQLAlchemy domain models created
- Alembic initial migration added
- JWT auth and refresh-token persistence added
- seed script for initial master admin added
- tenant-aware admin endpoints added for dashboard, users, profiles, reviews, templates, and Google account inventory
- Google OAuth start/callback, GBP sync, and Gemini reply generation hooks added
- worker and scheduler entrypoints scaffolded

## Current Frontend Progress

- login screen with persisted JWT session
- protected application shell
- API-backed dashboard
- homepage controls for Google connect and sync
- reviews page
- users page
- settings page for connected accounts and reply templates
# Google-Review-Automation

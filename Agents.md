Build a web-based Google Business Profile Management Dashboard for Kuttukaran and Maruti, who collectively manage 75+ Google Business Profiles across dealership locations in Kerala, currently split across two separate Google accounts. The goal is to unify profile management, automate review handling, improve accountability, and provide reporting in a single dashboard.

This product should follow a multi-tenant SaaS-style architecture, but the immediate implementation is based on the real business scope defined for Kuttukaran. The dashboard must support Google Business Profile integration through OAuth, review synchronization, automated replies, admin assignment, notifications, and analytics. The broader SaaS reference also expects secure OAuth credential storage, staff assignment by business, analytics, exports, and auditability.

Business Problem

Right now, reviews are monitored manually across many locations with no consolidated system, no defined ownership, no reliable escalation path for negative reviews, and no network-level reporting. This causes delayed responses, inconsistent customer handling, and weak operational visibility. The new app must solve this by centralizing all profiles, automating polling, routing responsibility clearly, and logging actions.

Target Users

There are two main user types for the first release:

Master Admin: can view and manage all profiles, configure admin assignments, manage templates/settings, and access aggregate reports.
Local Admin: can access only assigned branch profiles and handle reviews for those branches.

The broader product reference also defines more SaaS-friendly roles such as super admin, agency admin, staff/reviewer, and analyst. Design the codebase so role expansion is possible later even if the initial release only uses Master Admin and Local Admin.

Core Product Requirements

The application must provide a private web dashboard that connects to the Google Business Profile API and consolidates all connected profiles into a single interface. The home view should list profiles in a searchable and filterable table showing:

business name
location / city
current average rating
total review count
assigned local admin
last review activity timestamp
profile status (active/inactive)
Review Management Workflow

The system must poll Google Business Profile reviews at regular intervals. The real scope document specifies every 15 minutes.

Review handling rules:

Positive reviews (4–5 stars): generate an AI-personalized thank-you reply and post it automatically through the GBP API.
Negative reviews (1–3 stars): post a pre-approved templated apology automatically, then immediately alert the assigned Local Admin by email and WhatsApp.

Additional controls for Master Admin:

view all AI-generated responses
edit or override templates by brand (Maruti / Kuttukaran)
enable/disable auto-response per profile
view full audit log with timestamp and review ID.
Notifications

When a negative review is detected, alerts must be sent to the assigned Local Admin through:

Email
WhatsApp via Twilio WhatsApp Business API

Each Local Admin should be able to toggle email and WhatsApp alerts on or off. Master Admin must be able to see delivery status for each alert and edit notification templates without code deployment.

User and Admin Management

Master Admin must be able to:

add Local Admins
assign one or more profiles to them
edit assignments at any time
suspend/reactivate accounts
delete accounts with confirmation.

The broader SaaS planning document also expects role-based access control, staff-business assignments, and secure login flows. Build the auth and permission system with that extensibility in mind.

Reports and Analytics

Master Admin should have access to summary metrics and downloadable reports. Initial analytics should include:

total connected profiles
reviews received
positive vs negative review breakdown
AI response rate
alert delivery rate
average rating by profile and across the network
date range filters: last 7 days, 30 days, 90 days, custom
CSV export.

The larger SaaS vision also includes response time, sentiment trends, rating distribution, top/underperforming locations, side-by-side location comparison, and PDF/CSV export. Structure the analytics module so these can be added later.

Key Product Decisions

Respect these scope decisions:

AI should handle positive reviews, but not sensitive negative reviews beyond posting a pre-approved apology template.
Negative reviews must trigger branch-level accountability rather than central-team routing.
Alerts should go by both email and WhatsApp.
Initial release is web-only, no mobile app.
Google Integration Requirements

Use Google OAuth 2.0 for connecting Google accounts that have Business Profile access. Store access tokens and refresh tokens securely, with refresh tokens encrypted at rest. Important GBP endpoints include:

locations list
reviews list
update reply
delete reply.

The architecture should support more than one connected Google account because the current business setup spans two separate Google accounts.

Suggested Tech Direction

Preferred stack from the product plan:

Frontend: React + TypeScript + TailwindCSS
Backend: FastAPI or NestJS
Database: PostgreSQL
Queue/Cache: Redis
Background jobs: Celery if FastAPI is used
Charts: Recharts or Chart.js
Auth: JWT-based login for internal dashboard users
Email: Resend or SendGrid
WhatsApp: Twilio
Exports: CSV first, PDF later.
Database / Domain Model Guidance

Initial entities should include:

users
roles
local admin assignments
google accounts / oauth credentials
business profiles / locations
reviews
review replies
review templates
notification preferences
notifications / delivery logs
audit logs
analytics snapshots or aggregates.

This aligns with the SaaS schema guidance around tenants, businesses, credentials, staff, assignments, reviews, and replies, adapted for the Kuttukaran scope.

Development Priority

Build in this order:

Google OAuth connection and secure token storage
Fetch and store locations
Poll and sync reviews
Dashboard login and role-based access
Profile overview screen
Positive/negative review automation flow
Email and WhatsApp notifications
Admin assignment management
Reports and CSV export
Audit logs and settings/template management.
Important Constraints
First release is internal/admin-facing only.
No public customer portal.
No mobile app in v1.
Negative review handling must remain human-aware and auditable.
All actions should be logged with timestamps.
Code should be production-structured and easy to extend into a larger multi-tenant SaaS later.
Shorter prompt version for Codex

Build a production-ready web dashboard for managing 75+ Google Business Profiles across two Google accounts for Kuttukaran and Maruti. The app must unify all profiles into one dashboard with two roles: Master Admin and Local Admin. Master Admin can manage all profiles, users, assignments, templates, logs, and reports. Local Admin can access only assigned branch profiles. The system must connect using Google OAuth 2.0, securely store tokens, fetch locations, poll reviews every 15 minutes, and automate review workflows. For positive reviews (4–5 stars), generate and post an AI thank-you reply automatically. For negative reviews (1–3 stars), post a pre-approved apology template and send alerts to the assigned Local Admin by email and WhatsApp. Include a profile overview table, review management, template controls, alert delivery tracking, audit logs, analytics, and CSV export. Use a scalable architecture such as React + TypeScript + Tailwind + FastAPI + PostgreSQL + Redis + Celery. Structure the code so it can expand later into a broader multi-tenant SaaS review management platform.
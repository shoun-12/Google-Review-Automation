# Go-Live Test Cases

This document is the pre-release and go-live validation checklist for the Google Review Automation project.

The goal is to verify that the product is safe, functional, and ready for real usage before moving to production.

## Test Objective

We need to confirm that the application works correctly for:

- authentication
- role-based access
- Google OAuth
- GBP sync
- review reply automation
- local-admin visibility
- reporting
- auditability
- production-readiness basics

## Test Environments

Recommended environments:

- local development
- staging or pre-production
- production smoke test after deployment

## Pre-Test Requirements

Before running the full test suite, make sure the following are available:

- working PostgreSQL database
- working Redis instance
- backend and frontend deployed
- Celery worker running
- Celery beat running if scheduled sync is being tested
- valid Google OAuth credentials
- valid GBP API access
- valid `GOOGLE_TOKEN_ENCRYPTION_KEY`
- valid `JWT_SECRET_KEY`
- optional but recommended:
  - Gemini API key
  - email provider credentials
  - WhatsApp/Twilio credentials

## Test Data Setup

Prepare the following test data:

- 1 master admin account
- 2 local admin accounts
- multiple GBP profiles under the tenant
- at least:
  - 1 profile assigned to local admin A
  - 1 profile assigned to local admin B
  - 1 unassigned profile
- at least one connected Google account with accessible locations
- one profile with auto-response enabled
- one profile with auto-response disabled
- negative reply template configured

## Functional Test Cases

### 1. Login As Master Admin

Steps:

1. Open login page
2. Enter valid master admin credentials
3. Submit login form

Expected:

- login succeeds
- dashboard loads
- master admin menu items are visible
- session is persisted after reload

### 2. Login As Local Admin

Steps:

1. Open login page
2. Enter valid local admin credentials
3. Submit login form

Expected:

- login succeeds
- dashboard loads
- restricted navigation is shown
- local admin cannot access master-admin-only sections

### 3. Invalid Login

Steps:

1. Enter invalid email or password
2. Submit login form

Expected:

- login fails
- error message is shown
- no session is created

### 4. Session Persistence

Steps:

1. Login successfully
2. Reload the page

Expected:

- user remains logged in
- protected page still loads

### 5. Logout

Steps:

1. Login successfully
2. Click sign out

Expected:

- session is cleared
- user is redirected to login
- protected pages are no longer accessible

## Role And Access Test Cases

### 6. Master Admin Navigation Visibility

Expected:

- dashboard
- reports
- profiles
- reviews
- users
- settings
- audit logs

### 7. Local Admin Navigation Visibility

Expected:

- dashboard
- profiles
- reviews

Not expected:

- reports
- users
- settings
- audit logs

### 8. Local Admin Data Scope

Steps:

1. Login as local admin A
2. Open dashboard, profiles, and reviews

Expected:

- only assigned profiles are shown
- only reviews for assigned profiles are shown
- analytics are scoped to assigned profiles

### 9. Unassigned Profiles Visibility

Steps:

1. Login as local admin
2. Check profile list

Expected:

- unassigned profiles should not appear for local admins

## User Management Test Cases

### 10. Create Local Admin User

Steps:

1. Login as master admin
2. Open users page
3. Create a new local admin

Expected:

- user is created successfully
- user appears in the list
- audit log entry is created

### 11. Update User

Steps:

1. Change role, phone number, or alert settings

Expected:

- update persists
- user list reflects the change
- audit log entry is created

### 12. Suspend User

Steps:

1. Suspend an active user
2. Attempt login with that user

Expected:

- suspended user cannot log in

## Profile Management Test Cases

### 13. Assign Primary Local Admin To Profile

Steps:

1. Login as master admin
2. Open profiles page
3. assign a local admin

Expected:

- assignment is saved
- profile shows assigned admin
- local admin scope updates correctly
- audit log entry is created

### 14. Toggle Auto Response

Steps:

1. Disable auto response for a profile
2. Run sync with a review eligible for reply

Expected:

- no reply is posted for that profile

## Google OAuth And Integration Test Cases

### 15. Start Google OAuth

Steps:

1. Login as master admin
2. Click `Connect Google`

Expected:

- user is redirected to Google consent flow
- audit log records OAuth start

### 16. Complete Google OAuth

Steps:

1. Grant consent in Google
2. Return to app

Expected:

- success redirect occurs
- connected Google account is stored
- token is encrypted at rest

### 17. Google Account Inventory

Steps:

1. Open settings page

Expected:

- connected Google account appears
- scopes and account metadata are visible

### 18. Manual GBP Sync

Steps:

1. Click `Sync GBP`

Expected:

- sync completes
- synced account/location/review counts are shown
- profiles are created or updated
- reviews are created or updated
- audit log records sync trigger

## Review Reply Automation Test Cases

### 19. Positive Review Auto Reply

Precondition:

- profile has auto response enabled
- a positive review exists without a reply

Steps:

1. Run sync

Expected:

- positive review is detected
- reply text is generated
- reply is posted to Google
- reply record is stored locally
- review status becomes `REPLIED`

### 20. Positive Review Fallback Reply

Precondition:

- Gemini key is not configured

Steps:

1. Run sync on a positive review

Expected:

- fallback thank-you reply is used
- sync does not fail just because Gemini is absent

### 21. Negative Review Template Reply

Precondition:

- negative template exists and is active

Steps:

1. Run sync on a negative review

Expected:

- negative review is detected
- template reply is used
- reply is posted to Google
- review is marked `REPLIED`

### 22. Negative Review Fallback Reply

Precondition:

- no active negative template exists

Steps:

1. Run sync on a negative review

Expected:

- default apology reply is used
- review still gets processed

### 23. Auto Response Disabled Profile

Precondition:

- profile has auto response disabled

Steps:

1. Run sync on a review for that profile

Expected:

- no reply is posted
- review remains pending or unreplied

## Analytics And Dashboard Test Cases

### 24. Master Admin Dashboard Metrics

Expected:

- connected profiles count is correct
- reviews synced count is correct
- AI response rate is correct
- average rating is correct

### 25. Local Admin Dashboard Metrics

Expected:

- counts reflect only assigned profiles
- graphs render without errors
- values are scoped correctly

### 26. Trend Graph Label Accuracy

Expected:

- latest day count matches most recent day in returned trend data
- total review count in the window is accurate
- peak day label is accurate

## Reports Test Cases

### 27. Reports Overview For Master Admin

Steps:

1. Open reports page

Expected:

- summary loads
- profile ranking loads
- date window options work

### 28. CSV Export

Steps:

1. Export profiles CSV

Expected:

- download succeeds
- file contains correct column headers
- file contains accurate profile metrics

## Audit Log Test Cases

### 29. Audit Log Readability

Expected:

- logs display readable labels
- metadata is shown as UI fields, not raw JSON code blocks

### 30. Audit Coverage

Verify that logs exist for:

- login-related admin actions where applicable
- user creation
- user update
- profile update
- Google OAuth start
- Google sync trigger

## Theme And UI Test Cases

### 31. Light Mode

Expected:

- text is readable
- borders are visible
- sidebar colors match the rest of the app
- hover states are visible and consistent

### 32. Dark Mode

Steps:

1. Toggle dark mode from login page
2. Toggle dark mode from app shell

Expected:

- mode switches correctly
- setting persists after reload
- cards, panels, text, borders, inputs, and sidebar remain readable
- no section stays stuck in the wrong theme

### 33. Sidebar Behavior

Expected:

- expanded sidebar shows icon + label
- collapsed sidebar shows icon only
- mobile menu opens and closes correctly
- no overlap or broken alignment in collapsed mode

## Production Safety Test Cases

### 34. Secret Handling

Expected:

- `.env.example` contains placeholders only
- no real credentials are committed
- production secrets are provided through environment configuration

### 35. Error Handling

Expected:

- failed API calls show understandable messages
- OAuth failures return clear UI feedback
- sync errors do not crash the UI

### 36. Background Service Availability

Expected:

- API is healthy
- worker is healthy
- beat is healthy
- database is reachable
- Redis is reachable

## Manual Go-Live Checklist

Before go-live, confirm:

- all required environment variables are configured
- Google OAuth redirect URI matches deployed domain
- production database is migrated
- seed admin exists or admin creation path is ready
- worker and beat are running
- logging is enabled
- secrets are rotated and valid
- test sync succeeds against a real GBP account
- at least one positive and one negative review flow is validated

## Known Gaps To Recheck Before Production

These areas need extra attention because they are partially implemented or still evolving:

- automatic refresh-token usage in frontend
- email alert implementation
- WhatsApp alert implementation
- delivery tracking for alerts
- many-to-many profile assignment flow
- richer reporting and custom date filtering

## Test Result Template

Use this format while executing tests:

```text
Test ID:
Test Name:
Tester:
Date:
Environment:
Result: Pass / Fail / Blocked
Notes:
Screenshots / Evidence:
```

## Final Release Decision

The project should only be approved for live delivery when:

- all critical tests pass
- all medium-risk issues are accepted or fixed
- no live secrets are committed
- Google OAuth and GBP sync are validated on real data
- reply automation works as expected
- role-based access is verified
- the UI is stable in both light and dark modes

from fastapi import APIRouter

from app.api.v1.routes import audit_logs
from app.api.v1.routes import auth
from app.api.v1.routes import dashboard
from app.api.v1.routes import google_accounts
from app.api.v1.routes import profiles
from app.api.v1.routes import reply_templates
from app.api.v1.routes import reports
from app.api.v1.routes import reviews
from app.api.v1.routes import users


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(google_accounts.router, prefix="/google", tags=["google"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(reply_templates.router, prefix="/reply-templates", tags=["reply-templates"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])

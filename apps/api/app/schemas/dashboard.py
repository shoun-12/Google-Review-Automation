from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.google_accounts import GoogleAccountListItem
from app.schemas.profiles import ProfileListItem
from app.schemas.reports import SummaryReportResponse
from app.schemas.reviews import ReviewListItem
from app.schemas.templates import ReplyTemplateListItem
from app.schemas.users import UserListItem


class DashboardSyncStatus(BaseModel):
    action: str
    created_at: datetime
    metadata_json: dict


class DashboardResponse(BaseModel):
    summary: SummaryReportResponse
    profiles: list[ProfileListItem]
    reviews: list[ReviewListItem]
    users: list[UserListItem]
    google_accounts: list[GoogleAccountListItem]
    reply_templates: list[ReplyTemplateListItem]
    latest_sync: DashboardSyncStatus | None = None

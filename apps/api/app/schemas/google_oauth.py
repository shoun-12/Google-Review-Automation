from __future__ import annotations

from pydantic import BaseModel


class GoogleOAuthStartResponse(BaseModel):
    authorization_url: str


class GoogleSyncResponse(BaseModel):
    message: str
    connected_accounts: int
    synced_locations: int
    synced_reviews: int
    replies_posted: int
    errors: list[str] = []

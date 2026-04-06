from __future__ import annotations

from pydantic import BaseModel


class SummaryReportResponse(BaseModel):
    total_connected_profiles: int
    reviews_received: int
    positive_reviews: int
    negative_reviews: int
    ai_response_rate: float
    alert_delivery_rate: float
    average_rating_network: float


class TrendPoint(BaseModel):
    date: str
    reviews_received: int
    positive_reviews: int
    negative_reviews: int
    replies_posted: int
    avg_rating: float


class ProfilePerformanceItem(BaseModel):
    id: str
    business_name: str
    brand: str
    city: str | None
    state: str | None
    reviews_received: int
    positive_reviews: int
    negative_reviews: int
    replies_posted: int
    avg_rating: float
    response_rate: float


class ReportOverviewResponse(BaseModel):
    summary: SummaryReportResponse
    trend: list[TrendPoint]
    profiles: list[ProfilePerformanceItem]
    window_days: int

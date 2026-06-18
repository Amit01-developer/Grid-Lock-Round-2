from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class CountByType(BaseModel):
    violation_type: str
    count: int = Field(ge=0)


class CountByStatus(BaseModel):
    status: str
    count: int = Field(ge=0)


class CountByCamera(BaseModel):
    camera_id: UUID | None
    camera_name: str
    location_name: str
    count: int = Field(ge=0)


class TrendPoint(BaseModel):
    date: date
    count: int = Field(ge=0)


class DailyStatistic(BaseModel):
    date: date
    total: int = Field(ge=0)
    severity_score: int = Field(ge=0)
    safety_index: int = Field(ge=0, le=100)
    night_violations: int = Field(ge=0)
    school_zone_violations: int = Field(ge=0)


class WeeklyStatistic(BaseModel):
    week_start: date
    week_end: date
    total: int = Field(ge=0)
    severity_score: int = Field(ge=0)
    safety_index: int = Field(ge=0, le=100)


class SafetyIndex(BaseModel):
    score: int = Field(ge=0, le=100)
    total_severity: int = Field(ge=0)
    average_severity: float = Field(ge=0)
    risk_level: str
    night_violations: int = Field(ge=0)
    school_zone_violations: int = Field(ge=0)


class AnalyticsResponse(BaseModel):
    total_violations: int = Field(ge=0)
    pending_review: int = Field(ge=0)
    confirmed: int = Field(ge=0)
    rejected: int = Field(ge=0)
    by_type: list[CountByType]
    by_status: list[CountByStatus]
    by_camera: list[CountByCamera]
    trend: list[TrendPoint]
    daily_statistics: list[DailyStatistic]
    weekly_statistics: list[WeeklyStatistic]
    safety_index: SafetyIndex


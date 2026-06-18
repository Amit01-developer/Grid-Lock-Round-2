from uuid import UUID

from pydantic import BaseModel, Field


class HeatmapPoint(BaseModel):
    camera_id: UUID | None
    camera_name: str
    location_name: str
    latitude: float
    longitude: float
    intensity: int = Field(ge=0)
    severity_score: int = Field(default=0, ge=0)
    safety_index: int = Field(default=100, ge=0, le=100)
    dominant_violation_type: str | None = None


class HeatmapResponse(BaseModel):
    total_points: int = Field(ge=0)
    points: list[HeatmapPoint]


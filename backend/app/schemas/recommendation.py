from uuid import UUID

from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    id: str
    priority: str = Field(pattern="^(high|medium|low)$")
    title: str
    description: str
    camera_id: UUID | None = None
    camera_name: str | None = None
    location_name: str | None = None
    violation_type: str | None = None
    estimated_impact: str
    severity_score: int = Field(default=0, ge=0)
    action: str | None = None


class RecommendationResponse(BaseModel):
    generated_from_violations: int = Field(ge=0)
    safety_index: int = Field(default=100, ge=0, le=100)
    total_severity: int = Field(default=0, ge=0)
    recommendations: list[Recommendation]


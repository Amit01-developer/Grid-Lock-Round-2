from datetime import datetime

from app.models.camera import Camera
from app.models.enums import ViolationType
from app.models.violation import Violation


SEVERITY_WEIGHTS = {
    ViolationType.HELMET_NON_COMPLIANCE: 20,
    ViolationType.TRIPLE_RIDING: 30,
    ViolationType.WRONG_SIDE_DRIVING: 35,
    ViolationType.ILLEGAL_PARKING: 15,
}

NIGHT_TIME_WEIGHT = 10
SCHOOL_ZONE_WEIGHT = 15


class SeverityService:
    @staticmethod
    def score(
        violation_type: ViolationType,
        detected_at: datetime | None,
        camera: Camera | None = None,
    ) -> int:
        score = SEVERITY_WEIGHTS.get(violation_type, 0)
        if SeverityService.is_night_time(detected_at):
            score += NIGHT_TIME_WEIGHT
        if SeverityService.is_school_zone(camera):
            score += SCHOOL_ZONE_WEIGHT
        return score

    @staticmethod
    def score_violation(violation: Violation) -> int:
        return SeverityService.score(
            violation.violation_type,
            violation.detected_at,
            violation.camera,
        )

    @staticmethod
    def is_night_time(detected_at: datetime | None) -> bool:
        if detected_at is None:
            return False
        hour = detected_at.hour
        return hour >= 20 or hour < 6

    @staticmethod
    def is_school_zone(camera: Camera | None) -> bool:
        if camera is None:
            return False
        fields = [
            camera.name,
            camera.location_name,
            camera.road_name,
            camera.description,
        ]
        return any("school" in (value or "").lower() for value in fields)

    @staticmethod
    def safety_index(total_severity: int, violation_count: int) -> int:
        if violation_count <= 0:
            return 100
        average_severity = total_severity / violation_count
        volume_penalty = min(25, violation_count // 4)
        return max(0, min(100, round(100 - average_severity - volume_penalty)))


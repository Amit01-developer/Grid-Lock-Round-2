from app.ai.types import ViolationCandidate
from app.models.enums import ViolationType


BASE_SEVERITY = {
    ViolationType.HELMET_NON_COMPLIANCE: 62,
    ViolationType.TRIPLE_RIDING: 76,
    ViolationType.WRONG_SIDE_DRIVING: 92,
    ViolationType.ILLEGAL_PARKING: 58,
}


class SeverityScoreEngine:
    def score(self, violation: ViolationCandidate) -> float:
        base = BASE_SEVERITY[violation.violation_type]
        confidence_bonus = violation.confidence * 18
        plate_bonus = 5 if violation.plate_number else 0
        evidence_bonus = min(len(violation.related_detections), 4) * 2
        return round(min(100.0, base + confidence_bonus + plate_bonus + evidence_bonus), 2)


from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.camera import Camera
from app.models.enums import ViolationType
from app.models.violation import Violation
from app.schemas.heatmap import HeatmapPoint, HeatmapResponse
from app.services.severity_service import SeverityService


class HeatmapService:
    @staticmethod
    def get_heatmap(
        db: Session,
        *,
        days: int = 30,
        violation_type: ViolationType | None = None,
    ) -> HeatmapResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        filters = [Violation.detected_at >= since]
        if violation_type:
            filters.append(Violation.violation_type == violation_type)

        rows = db.execute(
            select(
                Camera.id.label("camera_id"),
                Camera.name.label("camera_name"),
                Camera.location_name.label("location_name"),
                Camera.latitude.label("latitude"),
                Camera.longitude.label("longitude"),
                Violation.violation_type.label("violation_type"),
                func.count(Violation.id).label("count"),
            )
            .join(Violation, Violation.camera_id == Camera.id)
            .where(*filters)
            .group_by(
                Camera.id,
                Camera.name,
                Camera.location_name,
                Camera.latitude,
                Camera.longitude,
                Violation.violation_type,
            )
        ).all()

        grouped: dict[str, dict] = {}
        type_counts: dict[str, dict[str, int]] = defaultdict(dict)
        severity_by_camera: dict[str, int] = defaultdict(int)
        violations = db.scalars(
            select(Violation)
            .options(joinedload(Violation.camera))
            .where(*filters, Violation.camera_id.is_not(None))
        ).all()
        for violation in violations:
            severity_by_camera[str(violation.camera_id)] += SeverityService.score_violation(violation)

        for row in rows:
            key = str(row.camera_id)
            grouped.setdefault(
                key,
                {
                    "camera_id": row.camera_id,
                    "camera_name": row.camera_name,
                    "location_name": row.location_name,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "intensity": 0,
                    "severity_score": 0,
                    "safety_index": 100,
                },
            )
            grouped[key]["intensity"] += row.count
            type_counts[key][str(row.violation_type)] = row.count

        points = []
        for key, item in grouped.items():
            dominant = max(type_counts[key].items(), key=lambda entry: entry[1])[0] if type_counts[key] else None
            item["severity_score"] = severity_by_camera[key]
            item["safety_index"] = SeverityService.safety_index(item["severity_score"], item["intensity"])
            points.append(HeatmapPoint(**item, dominant_violation_type=dominant))

        points.sort(key=lambda point: point.intensity, reverse=True)
        return HeatmapResponse(total_points=len(points), points=points)


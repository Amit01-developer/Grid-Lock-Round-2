from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.camera import Camera
from app.models.enums import ViolationStatus
from app.models.violation import Violation
from app.schemas.analytics import (
    AnalyticsResponse,
    CountByCamera,
    CountByStatus,
    CountByType,
    DailyStatistic,
    SafetyIndex,
    TrendPoint,
    WeeklyStatistic,
)
from app.services.severity_service import SeverityService


class AnalyticsService:
    @staticmethod
    def get_analytics(db: Session, days: int = 30) -> AnalyticsResponse:
        since = datetime.now(UTC) - timedelta(days=days)
        filters = [Violation.detected_at >= since]

        total = db.scalar(select(func.count(Violation.id)).where(*filters)) or 0
        status_counts = dict(
            db.execute(
                select(Violation.status, func.count(Violation.id))
                .where(*filters)
                .group_by(Violation.status)
            ).all()
        )

        by_type = [
            CountByType(violation_type=str(row[0]), count=row[1])
            for row in db.execute(
                select(Violation.violation_type, func.count(Violation.id))
                .where(*filters)
                .group_by(Violation.violation_type)
                .order_by(func.count(Violation.id).desc())
            ).all()
        ]

        by_status = [
            CountByStatus(status=str(status), count=count)
            for status, count in status_counts.items()
        ]

        by_camera = [
            CountByCamera(
                camera_id=row.camera_id,
                camera_name=row.camera_name or "Unassigned camera",
                location_name=row.location_name or "Unknown location",
                count=row.count,
            )
            for row in db.execute(
                select(
                    Violation.camera_id.label("camera_id"),
                    Camera.name.label("camera_name"),
                    Camera.location_name.label("location_name"),
                    func.count(Violation.id).label("count"),
                )
                .outerjoin(Camera, Violation.camera_id == Camera.id)
                .where(*filters)
                .group_by(Violation.camera_id, Camera.name, Camera.location_name)
                .order_by(func.count(Violation.id).desc())
            ).all()
        ]

        detected_day = func.date(Violation.detected_at)
        trend = [
            TrendPoint(date=row.day, count=row.count)
            for row in db.execute(
                select(
                    detected_day.label("day"),
                    func.count(Violation.id).label("count"),
                )
                .where(*filters)
                .group_by(detected_day)
                .order_by(detected_day)
            ).all()
        ]

        violations = db.scalars(
            select(Violation)
            .options(joinedload(Violation.camera))
            .where(*filters)
            .order_by(Violation.detected_at)
        ).all()
        daily_statistics = AnalyticsService._daily_statistics(violations)
        weekly_statistics = AnalyticsService._weekly_statistics(violations)
        total_severity = sum(SeverityService.score_violation(item) for item in violations)
        night_violations = sum(1 for item in violations if SeverityService.is_night_time(item.detected_at))
        school_zone_violations = sum(1 for item in violations if SeverityService.is_school_zone(item.camera))
        safety_score = SeverityService.safety_index(total_severity, len(violations))

        return AnalyticsResponse(
            total_violations=total,
            pending_review=status_counts.get(ViolationStatus.PENDING_REVIEW, 0),
            confirmed=status_counts.get(ViolationStatus.CONFIRMED, 0),
            rejected=status_counts.get(ViolationStatus.REJECTED, 0),
            by_type=by_type,
            by_status=by_status,
            by_camera=by_camera,
            trend=trend,
            daily_statistics=daily_statistics,
            weekly_statistics=weekly_statistics,
            safety_index=SafetyIndex(
                score=safety_score,
                total_severity=total_severity,
                average_severity=round(total_severity / len(violations), 2) if violations else 0,
                risk_level=AnalyticsService._risk_level(safety_score),
                night_violations=night_violations,
                school_zone_violations=school_zone_violations,
            ),
        )

    @staticmethod
    def _daily_statistics(violations: list[Violation]) -> list[DailyStatistic]:
        grouped: dict = defaultdict(lambda: {"total": 0, "severity": 0, "night": 0, "school": 0})
        for violation in violations:
            day = violation.detected_at.date()
            grouped[day]["total"] += 1
            grouped[day]["severity"] += SeverityService.score_violation(violation)
            grouped[day]["night"] += int(SeverityService.is_night_time(violation.detected_at))
            grouped[day]["school"] += int(SeverityService.is_school_zone(violation.camera))

        return [
            DailyStatistic(
                date=day,
                total=item["total"],
                severity_score=item["severity"],
                safety_index=SeverityService.safety_index(item["severity"], item["total"]),
                night_violations=item["night"],
                school_zone_violations=item["school"],
            )
            for day, item in sorted(grouped.items())
        ]

    @staticmethod
    def _weekly_statistics(violations: list[Violation]) -> list[WeeklyStatistic]:
        grouped: dict = defaultdict(lambda: {"total": 0, "severity": 0})
        for violation in violations:
            day = violation.detected_at.date()
            week_start = day - timedelta(days=day.weekday())
            grouped[week_start]["total"] += 1
            grouped[week_start]["severity"] += SeverityService.score_violation(violation)

        return [
            WeeklyStatistic(
                week_start=week_start,
                week_end=week_start + timedelta(days=6),
                total=item["total"],
                severity_score=item["severity"],
                safety_index=SeverityService.safety_index(item["severity"], item["total"]),
            )
            for week_start, item in sorted(grouped.items())
        ]

    @staticmethod
    def _risk_level(score: int) -> str:
        if score >= 80:
            return "low"
        if score >= 60:
            return "moderate"
        if score >= 40:
            return "high"
        return "critical"

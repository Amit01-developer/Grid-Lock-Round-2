from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.models.enums import ObjectType, ViolationType


Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class PreprocessedImage:
    original: Any
    inference: Any
    path: Path
    width: int
    height: int
    scale_x: float = 1.0
    scale_y: float = 1.0


@dataclass(frozen=True)
class ObjectDetection:
    label: str
    object_type: ObjectType
    confidence: float
    bbox: Box
    class_id: int | None = None
    track_id: str | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]

    def scaled(self, scale_x: float, scale_y: float) -> "ObjectDetection":
        x1, y1, x2, y2 = self.bbox
        return ObjectDetection(
            label=self.label,
            object_type=self.object_type,
            confidence=self.confidence,
            bbox=(
                int(round(x1 * scale_x)),
                int(round(y1 * scale_y)),
                int(round(x2 * scale_x)),
                int(round(y2 * scale_y)),
            ),
            class_id=self.class_id,
            track_id=self.track_id,
            metadata=self.metadata,
        )


@dataclass(frozen=True)
class PlateOCR:
    plate_number: str
    confidence: float
    bbox: Box | None = None
    cropped_plate_path: Path | None = None
    cropped_plate_url: str | None = None


@dataclass(frozen=True)
class ViolationCandidate:
    violation_type: ViolationType
    confidence: float
    vehicle_type: str | None
    plate_number: str | None
    primary_detection: ObjectDetection | None
    related_detections: list[ObjectDetection]
    severity_score: float = 0.0
    notes: str = ""

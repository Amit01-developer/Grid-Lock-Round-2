from dataclasses import dataclass, field, replace
from pathlib import Path

from app.ai.annotation import EvidenceGenerator
from app.ai.detection import YOLOv8Detector
from app.ai.ocr import LicensePlateOCR
from app.ai.preprocessing import ImagePreprocessor
from app.ai.severity import SeverityScoreEngine
from app.ai.violations import ViolationDetector
from app.config.settings import settings
from app.models.enums import ObjectType, ViolationType
from app.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass(frozen=True)
class DetectionPayload:
    object_type: ObjectType
    confidence: float
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    track_id: str | None = None
    metadata: dict | None = None


@dataclass(frozen=True)
class OCRPayload:
    plate_number: str
    confidence: float
    cropped_plate_url: str | None = None


@dataclass(frozen=True)
class EvidencePayload:
    evidence_image_url: str
    cropped_vehicle_url: str | None = None
    annotated_image_url: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class ViolationPayload:
    violation_type: ViolationType
    confidence: float
    vehicle_type: str | None = None
    plate_number: str | None = None
    evidence: list[EvidencePayload] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineResult:
    detections: list[DetectionPayload] = field(default_factory=list)
    ocr_results: list[OCRPayload] = field(default_factory=list)
    violations: list[ViolationPayload] = field(default_factory=list)
    image_width: int | None = None
    image_height: int | None = None


class AIPipelineService:
    """Runs image preprocessing, YOLOv8, OCR, rules, scoring, and evidence output."""

    def __init__(
        self,
        preprocessor: ImagePreprocessor | None = None,
        violation_detector: ViolationDetector | None = None,
        severity_engine: SeverityScoreEngine | None = None,
        evidence_generator: EvidenceGenerator | None = None,
    ) -> None:
        self.preprocessor = preprocessor or ImagePreprocessor()
        self.violation_detector = violation_detector or ViolationDetector()
        self.severity_engine = severity_engine or SeverityScoreEngine()
        self.evidence_generator = evidence_generator or EvidenceGenerator()

    def process(self, image_path: Path) -> PipelineResult:
        if not settings.ai_processing_enabled:
            logger.info("AI processing disabled; image stored without inference.", extra={"image": str(image_path)})
            return PipelineResult()

        if not settings.yolo_model_path:
            logger.warning("AI processing enabled but YOLO_MODEL_PATH is not configured.")
            return PipelineResult()

        prepared = self.preprocessor.load(image_path)
        output_dir = self._evidence_output_dir(image_path)

        detector = YOLOv8Detector(
            model_path=settings.yolo_model_path,
            confidence_threshold=settings.yolo_confidence_threshold,
            image_size=settings.yolo_image_size,
        )
        ocr = LicensePlateOCR(
            languages=settings.ocr_languages,
            min_confidence=settings.ocr_min_confidence,
        )

        detections = [
            item.scaled(prepared.scale_x, prepared.scale_y)
            for item in detector.detect(prepared.inference)
        ]
        ocr_results = ocr.read_plates(prepared.original, detections, output_dir)
        violations = self.violation_detector.detect(detections, ocr_results)
        scored_violations = [
            replace(violation, severity_score=self.severity_engine.score(violation))
            for violation in violations
        ]
        evidence_records = self.evidence_generator.generate(prepared.original, scored_violations, output_dir)

        logger.info(
            "AI pipeline completed.",
            extra={
                "image": str(image_path),
                "detections": len(detections),
                "ocr_results": len(ocr_results),
                "violations": len(scored_violations),
            },
        )

        return PipelineResult(
            detections=[
                DetectionPayload(
                    object_type=item.object_type,
                    confidence=item.confidence,
                    bbox_x=item.x,
                    bbox_y=item.y,
                    bbox_width=item.width,
                    bbox_height=item.height,
                    track_id=item.track_id,
                    metadata={
                        **item.metadata,
                        "label": item.label,
                        "class_id": item.class_id,
                    },
                )
                for item in detections
            ],
            ocr_results=[
                OCRPayload(
                    plate_number=item.plate_number,
                    confidence=item.confidence,
                    cropped_plate_url=item.cropped_plate_url,
                )
                for item in ocr_results
            ],
            violations=[
                ViolationPayload(
                    violation_type=item.violation_type,
                    confidence=item.confidence,
                    vehicle_type=item.vehicle_type,
                    plate_number=item.plate_number,
                    evidence=[
                        EvidencePayload(
                            evidence_image_url=evidence["evidence_image_url"],
                            cropped_vehicle_url=evidence["cropped_vehicle_url"],
                            annotated_image_url=evidence["annotated_image_url"],
                            notes=evidence["notes"],
                        )
                    ],
                )
                for item, evidence in zip(scored_violations, evidence_records, strict=False)
            ],
            image_width=prepared.width,
            image_height=prepared.height,
        )

    @staticmethod
    def _evidence_output_dir(image_path: Path) -> Path:
        output_dir = settings.upload_dir / settings.evidence_dir_name / image_path.stem
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


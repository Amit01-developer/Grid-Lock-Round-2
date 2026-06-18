from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.models.detection import Detection, OCRResult
from app.models.enums import ImageProcessingStatus
from app.models.image import UploadedImage
from app.models.violation import Violation, ViolationEvidence
from app.services.ai_pipeline import AIPipelineService, PipelineResult
from app.services.storage_service import StorageService
from app.utils.exceptions import NotFoundError
from app.utils.logging import get_logger


logger = get_logger(__name__)


class UploadService:
    def __init__(
        self,
        storage_service: StorageService | None = None,
        ai_pipeline: AIPipelineService | None = None,
    ) -> None:
        self.storage_service = storage_service or StorageService()
        self.ai_pipeline = ai_pipeline or AIPipelineService()

    async def upload_image(
        self,
        db: Session,
        file,
        camera_id: UUID | None = None,
        captured_at: datetime | None = None,
    ) -> tuple[UploadedImage, int]:
        camera = self._get_camera(db, camera_id) if camera_id else None
        stored_file = await self.storage_service.save_upload(file)

        image = UploadedImage(
            camera_id=camera.id if camera else None,
            file_name=stored_file.file_name,
            original_filename=stored_file.original_filename,
            content_type=stored_file.content_type,
            file_size_bytes=stored_file.file_size_bytes,
            image_url=stored_file.url,
            captured_at=captured_at,
            processing_status=ImageProcessingStatus.PENDING,
        )

        try:
            db.add(image)
            db.flush()

            image.processing_status = ImageProcessingStatus.PROCESSING
            result = self.ai_pipeline.process(stored_file.path)
            image.width = result.image_width
            image.height = result.image_height
            detected_violations = self._persist_pipeline_result(db, image, result)

            image.processing_status = ImageProcessingStatus.COMPLETED
            db.commit()
            db.refresh(image)
            logger.info("Image uploaded successfully.", extra={"image_id": str(image.id)})
            return image, detected_violations
        except Exception:
            db.rollback()
            self.storage_service.delete_file(stored_file.path)
            logger.exception("Image upload transaction failed.")
            raise

    @staticmethod
    def _get_camera(db: Session, camera_id: UUID) -> Camera:
        camera = db.get(Camera, camera_id)
        if not camera:
            raise NotFoundError("Camera not found.", details={"camera_id": str(camera_id)})
        return camera

    @staticmethod
    def _persist_pipeline_result(db: Session, image: UploadedImage, result: PipelineResult) -> int:
        for item in result.detections:
            db.add(
                Detection(
                    image_id=image.id,
                    object_type=item.object_type,
                    confidence=item.confidence,
                    bbox_x=item.bbox_x,
                    bbox_y=item.bbox_y,
                    bbox_width=item.bbox_width,
                    bbox_height=item.bbox_height,
                    track_id=item.track_id,
                    extra_data=item.metadata,
                )
            )

        for item in result.ocr_results:
            db.add(
                OCRResult(
                    image_id=image.id,
                    plate_number=item.plate_number,
                    confidence=item.confidence,
                    cropped_plate_url=item.cropped_plate_url,
                )
            )

        for item in result.violations:
            violation = Violation(
                image_id=image.id,
                camera_id=image.camera_id,
                violation_type=item.violation_type,
                vehicle_type=item.vehicle_type,
                plate_number=item.plate_number,
                confidence=item.confidence,
            )
            for evidence in item.evidence:
                violation.evidence.append(
                    ViolationEvidence(
                        evidence_image_url=evidence.evidence_image_url,
                        cropped_vehicle_url=evidence.cropped_vehicle_url,
                        annotated_image_url=evidence.annotated_image_url,
                        notes=evidence.notes,
                    )
                )
            db.add(violation)

        return len(result.violations)


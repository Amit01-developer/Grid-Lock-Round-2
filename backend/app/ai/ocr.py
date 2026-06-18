import re
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from app.ai.types import ObjectDetection, PlateOCR
from app.config.settings import settings
from app.models.enums import ObjectType
from app.utils.logging import get_logger


logger = get_logger(__name__)
PLATE_PATTERN = re.compile(r"[^A-Z0-9]")


class LicensePlateOCR:
    def __init__(self, languages: list[str] | None = None, min_confidence: float = 0.25) -> None:
        self.languages = languages or settings.ocr_languages
        self.min_confidence = min_confidence
        self.reader = _load_reader(tuple(self.languages))

    def read_plates(self, image, detections: list[ObjectDetection], output_dir: Path) -> list[PlateOCR]:
        import cv2

        plate_detections = [item for item in detections if item.object_type == ObjectType.LICENSE_PLATE]
        results: list[PlateOCR] = []

        for detection in plate_detections:
            crop = crop_image(image, detection.bbox)
            if crop.size == 0:
                continue
            prepared = self._prepare_crop(crop)
            ocr_items = self.reader.readtext(prepared, detail=1, paragraph=False)
            plate_number, confidence = self._best_plate(ocr_items)
            if not plate_number or confidence < self.min_confidence:
                continue

            crop_path = output_dir / f"plate-{uuid4().hex}.jpg"
            cv2.imwrite(str(crop_path), crop)
            results.append(
                PlateOCR(
                    plate_number=plate_number,
                    confidence=confidence,
                    bbox=detection.bbox,
                    cropped_plate_path=crop_path,
                    cropped_plate_url=to_upload_url(crop_path),
                )
            )

        logger.info("License plate OCR completed.", extra={"plates": len(results)})
        return results

    @staticmethod
    def _prepare_crop(crop):
        import cv2

        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 7, 45, 45)
        return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    @staticmethod
    def _best_plate(ocr_items) -> tuple[str | None, float]:
        best_text = None
        best_score = 0.0
        for _, text, score in ocr_items:
            normalized = PLATE_PATTERN.sub("", text.upper())
            if len(normalized) >= 5 and score > best_score:
                best_text = normalized[:16]
                best_score = float(score)
        return best_text, best_score


def crop_image(image, bbox):
    height, width = image.shape[:2]
    x1 = max(0, min(width, bbox[0]))
    y1 = max(0, min(height, bbox[1]))
    x2 = max(0, min(width, bbox[2]))
    y2 = max(0, min(height, bbox[3]))
    return image[y1:y2, x1:x2]


def to_upload_url(path: Path) -> str:
    try:
        return f"/uploads/{path.relative_to(settings.upload_dir).as_posix()}"
    except ValueError:
        return f"/uploads/{path.name}"


@lru_cache(maxsize=4)
def _load_reader(languages: tuple[str, ...]):
    import easyocr

    return easyocr.Reader(list(languages), gpu=False)

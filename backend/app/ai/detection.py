from functools import lru_cache
from pathlib import Path

from app.ai.types import ObjectDetection
from app.models.enums import ObjectType
from app.utils.logging import get_logger


logger = get_logger(__name__)

LABEL_TO_OBJECT_TYPE = {
    "motorcycle": ObjectType.MOTORCYCLE,
    "motorbike": ObjectType.MOTORCYCLE,
    "bike": ObjectType.MOTORCYCLE,
    "person": ObjectType.RIDER,
    "rider": ObjectType.RIDER,
    "helmet": ObjectType.HELMET,
    "no_helmet": ObjectType.NO_HELMET,
    "no helmet": ObjectType.NO_HELMET,
    "without_helmet": ObjectType.NO_HELMET,
    "car": ObjectType.CAR,
    "truck": ObjectType.TRUCK,
    "bus": ObjectType.BUS,
    "license_plate": ObjectType.LICENSE_PLATE,
    "licence_plate": ObjectType.LICENSE_PLATE,
    "number_plate": ObjectType.LICENSE_PLATE,
    "plate": ObjectType.LICENSE_PLATE,
}


class YOLOv8Detector:
    def __init__(
        self,
        model_path: Path,
        confidence_threshold: float = 0.35,
        image_size: int = 960,
    ) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.image_size = image_size
        self.model = _load_model(str(model_path))

    def detect(self, image) -> list[ObjectDetection]:
        results = self.model.predict(
            image,
            conf=self.confidence_threshold,
            imgsz=self.image_size,
            verbose=False,
        )
        detections: list[ObjectDetection] = []
        for result in results:
            names = result.names or {}
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                label = str(names.get(class_id, class_id)).lower().strip().replace("-", "_")
                confidence = float(box.conf[0].item())
                x1, y1, x2, y2 = [int(round(value)) for value in box.xyxy[0].tolist()]
                object_type = LABEL_TO_OBJECT_TYPE.get(label, ObjectType.UNKNOWN)
                detections.append(
                    ObjectDetection(
                        label=label,
                        object_type=object_type,
                        confidence=confidence,
                        bbox=(x1, y1, x2, y2),
                        class_id=class_id,
                        metadata={"model_path": str(self.model_path), "raw_label": label},
                    )
                )

        logger.info("YOLOv8 detection completed.", extra={"detections": len(detections)})
        return detections


@lru_cache(maxsize=2)
def _load_model(model_path: str):
    from ultralytics import YOLO

    return YOLO(model_path)

from pathlib import Path

from app.ai.ocr import crop_image, to_upload_url
from app.ai.types import ViolationCandidate
from app.models.enums import ViolationType


COLORS = {
    ViolationType.HELMET_NON_COMPLIANCE: (0, 165, 255),
    ViolationType.TRIPLE_RIDING: (0, 0, 255),
    ViolationType.WRONG_SIDE_DRIVING: (0, 0, 180),
    ViolationType.ILLEGAL_PARKING: (42, 42, 165),
}


class EvidenceGenerator:
    def generate(self, image, violations: list[ViolationCandidate], output_dir: Path) -> list[dict]:
        import cv2

        evidence = []
        for index, violation in enumerate(violations, start=1):
            annotated = image.copy()
            color = COLORS[violation.violation_type]
            for detection in violation.related_detections:
                x1, y1, x2, y2 = detection.bbox
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            label = f"{violation.violation_type.value} | severity {violation.severity_score:.0f}"
            self._draw_label(annotated, label, violation.primary_detection, color)

            stem = f"{violation.violation_type.value}-{index}"
            annotated_path = output_dir / f"{stem}-annotated.jpg"
            cv2.imwrite(str(annotated_path), annotated)

            crop_url = None
            if violation.primary_detection:
                crop = crop_image(image, violation.primary_detection.bbox)
                if crop.size:
                    crop_path = output_dir / f"{stem}-vehicle.jpg"
                    cv2.imwrite(str(crop_path), crop)
                    crop_url = to_upload_url(crop_path)

            evidence.append(
                {
                    "evidence_image_url": to_upload_url(annotated_path),
                    "annotated_image_url": to_upload_url(annotated_path),
                    "cropped_vehicle_url": crop_url,
                    "notes": self._notes(violation),
                }
            )
        return evidence

    @staticmethod
    def _draw_label(image, label: str, primary_detection, color) -> None:
        import cv2

        x = 16
        y = 30
        if primary_detection:
            x = max(8, primary_detection.bbox[0])
            y = max(28, primary_detection.bbox[1] - 8)
        cv2.rectangle(image, (x, y - 22), (x + min(520, len(label) * 10), y + 6), color, -1)
        cv2.putText(image, label, (x + 6, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

    @staticmethod
    def _notes(violation: ViolationCandidate) -> str:
        parts = [violation.notes, f"Severity score: {violation.severity_score:.2f}/100"]
        if violation.plate_number:
            parts.append(f"Plate: {violation.plate_number}")
        return " ".join(part for part in parts if part)

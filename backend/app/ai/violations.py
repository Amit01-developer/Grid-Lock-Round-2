from collections import defaultdict

from app.ai.geometry import contains_center, overlap_ratio
from app.ai.types import ObjectDetection, PlateOCR, ViolationCandidate
from app.models.enums import ObjectType, ViolationType


DIRECT_VIOLATION_LABELS = {
    "helmet_non_compliance": ViolationType.HELMET_NON_COMPLIANCE,
    "no_helmet_violation": ViolationType.HELMET_NON_COMPLIANCE,
    "triple_riding": ViolationType.TRIPLE_RIDING,
    "wrong_side_driving": ViolationType.WRONG_SIDE_DRIVING,
    "wrong_way": ViolationType.WRONG_SIDE_DRIVING,
    "illegal_parking": ViolationType.ILLEGAL_PARKING,
    "parking_violation": ViolationType.ILLEGAL_PARKING,
}


class ViolationDetector:
    def detect(
        self,
        detections: list[ObjectDetection],
        ocr_results: list[PlateOCR],
    ) -> list[ViolationCandidate]:
        candidates: list[ViolationCandidate] = []
        candidates.extend(self._direct_model_violations(detections, ocr_results))
        candidates.extend(self._helmet_non_compliance(detections, ocr_results))
        candidates.extend(self._triple_riding(detections, ocr_results))
        return self._deduplicate(candidates)

    def _direct_model_violations(
        self,
        detections: list[ObjectDetection],
        ocr_results: list[PlateOCR],
    ) -> list[ViolationCandidate]:
        candidates = []
        for detection in detections:
            violation_type = DIRECT_VIOLATION_LABELS.get(detection.label)
            if not violation_type:
                continue
            candidates.append(
                ViolationCandidate(
                    violation_type=violation_type,
                    confidence=detection.confidence,
                    vehicle_type=self._vehicle_type_for(detection),
                    plate_number=self._nearest_plate(detection, ocr_results),
                    primary_detection=detection,
                    related_detections=[detection],
                    notes=f"Detected by model class '{detection.label}'.",
                )
            )
        return candidates

    def _helmet_non_compliance(
        self,
        detections: list[ObjectDetection],
        ocr_results: list[PlateOCR],
    ) -> list[ViolationCandidate]:
        no_helmet = [item for item in detections if item.object_type == ObjectType.NO_HELMET]
        motorcycles = [item for item in detections if item.object_type == ObjectType.MOTORCYCLE]
        candidates = []
        for detection in no_helmet:
            vehicle = self._containing_vehicle(detection, motorcycles) or detection
            candidates.append(
                ViolationCandidate(
                    violation_type=ViolationType.HELMET_NON_COMPLIANCE,
                    confidence=detection.confidence,
                    vehicle_type=self._vehicle_type_for(vehicle),
                    plate_number=self._nearest_plate(vehicle, ocr_results),
                    primary_detection=vehicle,
                    related_detections=[vehicle, detection] if vehicle is not detection else [detection],
                    notes="Rider detected without helmet.",
                )
            )
        return candidates

    def _triple_riding(
        self,
        detections: list[ObjectDetection],
        ocr_results: list[PlateOCR],
    ) -> list[ViolationCandidate]:
        motorcycles = [item for item in detections if item.object_type == ObjectType.MOTORCYCLE]
        riders = [item for item in detections if item.object_type == ObjectType.RIDER]
        candidates = []

        for motorcycle in motorcycles:
            riders_on_vehicle = [
                rider
                for rider in riders
                if contains_center(motorcycle, rider) or overlap_ratio(rider.bbox, motorcycle.bbox) >= 0.2
            ]
            if len(riders_on_vehicle) < 3:
                continue

            confidence = min(0.99, (motorcycle.confidence + sum(r.confidence for r in riders_on_vehicle[:3])) / 4)
            candidates.append(
                ViolationCandidate(
                    violation_type=ViolationType.TRIPLE_RIDING,
                    confidence=confidence,
                    vehicle_type="motorcycle",
                    plate_number=self._nearest_plate(motorcycle, ocr_results),
                    primary_detection=motorcycle,
                    related_detections=[motorcycle, *riders_on_vehicle],
                    notes=f"{len(riders_on_vehicle)} riders detected on one motorcycle.",
                )
            )
        return candidates

    @staticmethod
    def _containing_vehicle(
        detection: ObjectDetection,
        vehicles: list[ObjectDetection],
    ) -> ObjectDetection | None:
        for vehicle in vehicles:
            if contains_center(vehicle, detection) or overlap_ratio(detection.bbox, vehicle.bbox) >= 0.15:
                return vehicle
        return None

    @staticmethod
    def _nearest_plate(detection: ObjectDetection, ocr_results: list[PlateOCR]) -> str | None:
        if not ocr_results:
            return None
        for result in ocr_results:
            if result.bbox and overlap_ratio(result.bbox, detection.bbox) > 0:
                return result.plate_number
        return ocr_results[0].plate_number

    @staticmethod
    def _vehicle_type_for(detection: ObjectDetection | None) -> str | None:
        if detection is None:
            return None
        if detection.object_type == ObjectType.UNKNOWN:
            return None
        return detection.object_type.value

    @staticmethod
    def _deduplicate(candidates: list[ViolationCandidate]) -> list[ViolationCandidate]:
        grouped: dict[tuple[ViolationType, tuple[int, int, int, int] | None], list[ViolationCandidate]] = defaultdict(list)
        for candidate in candidates:
            key = (
                candidate.violation_type,
                candidate.primary_detection.bbox if candidate.primary_detection else None,
            )
            grouped[key].append(candidate)

        return [max(group, key=lambda item: item.confidence) for group in grouped.values()]


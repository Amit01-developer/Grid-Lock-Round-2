from app.ai.types import Box, ObjectDetection


def area(box: Box) -> int:
    return max(0, box[2] - box[0]) * max(0, box[3] - box[1])


def intersection_area(a: Box, b: Box) -> int:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    return area((x1, y1, x2, y2))


def overlap_ratio(inner: Box, outer: Box) -> float:
    inner_area = area(inner)
    if inner_area == 0:
        return 0.0
    return intersection_area(inner, outer) / inner_area


def center(box: Box) -> tuple[float, float]:
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def contains_center(container: ObjectDetection, item: ObjectDetection) -> bool:
    cx, cy = center(item.bbox)
    x1, y1, x2, y2 = container.bbox
    return x1 <= cx <= x2 and y1 <= cy <= y2


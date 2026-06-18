from pathlib import Path

from app.ai.types import PreprocessedImage
from app.utils.exceptions import ValidationError


class ImagePreprocessor:
    def __init__(self, max_dimension: int = 1280) -> None:
        self.max_dimension = max_dimension

    def load(self, image_path: Path) -> PreprocessedImage:
        import cv2

        image = cv2.imread(str(image_path))
        if image is None:
            raise ValidationError("Uploaded file could not be decoded as an image.")

        height, width = image.shape[:2]
        inference = self._resize_for_inference(image)
        inference = cv2.convertScaleAbs(inference, alpha=1.05, beta=4)
        inference_height, inference_width = inference.shape[:2]

        return PreprocessedImage(
            original=image,
            inference=inference,
            path=image_path,
            width=width,
            height=height,
            scale_x=width / inference_width,
            scale_y=height / inference_height,
        )

    def _resize_for_inference(self, image):
        import cv2

        height, width = image.shape[:2]
        longest_side = max(height, width)
        if longest_side <= self.max_dimension:
            return image.copy()

        scale = self.max_dimension / longest_side
        target_size = (int(width * scale), int(height * scale))
        return cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)

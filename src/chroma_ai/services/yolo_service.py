import logging
from typing import List

from cv2.typing import MatLike
from ultralytics import YOLO

from src.chroma_ai.config.config import MODEL_PATH

logger = logging.getLogger(__name__)


class YoloService:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def predict(self, image: MatLike) -> List[list[float | int]]:
        """Predict bounding boxes in the image using YOLO"""
        results = self.model.predict(image)

        if results and results[0].boxes.data is not None:
            boxes = results[0].boxes.data.cpu().numpy().tolist()
            boxes = [[round(x, 2) for x in box] for box in boxes]
            return boxes
        return []


yolo_service = YoloService()
logger.info("YoloService initialized successfully")

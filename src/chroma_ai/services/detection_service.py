import logging
from datetime import datetime
from typing import List, Callable

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO

from src.chroma_ai.config.config import MODEL_PATH

logger = logging.getLogger(__name__)

from enum import Enum
from typing import Tuple


class TrafficLightColor(Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Human-readable name for UI display"""
        return self.value.upper()

    @property
    def color_rgb(self) -> Tuple[int, int, int]:
        """RGB color values for UI display"""
        if self == TrafficLightColor.RED:
            return 255, 0, 0
        elif self == TrafficLightColor.YELLOW:
            return 255, 255, 0
        elif self == TrafficLightColor.GREEN:
            return 0, 255, 0
        return 128, 128, 128


class DetectionEvent:
    def __init__(self, color: TrafficLightColor, confidence: float, bbox: List[float], timestamp: datetime):
        self.color = color
        self.confidence = confidence
        self.bbox = bbox
        self.timestamp = timestamp


class DetectionService:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self._observers: List[Callable[[DetectionEvent], None]] = []
        self._image_observers: List[Callable[[MatLike], None]] = []

    def add_observer(self, observer: Callable[[DetectionEvent], None]):
        """Add observer for detection events"""
        self._observers.append(observer)

    def remove_observer(self, observer: Callable[[DetectionEvent], None]):
        """Remove observer for detection events"""
        if observer in self._observers:
            self._observers.remove(observer)

    def add_image_observer(self, observer: Callable[[MatLike], None]):
        """Add observer for processed images with bounding boxes"""
        self._image_observers.append(observer)

    def remove_image_observer(self, observer: Callable[[MatLike], None]):
        """Remove observer for processed images"""
        if observer in self._image_observers:
            self._image_observers.remove(observer)

    def _notify_observers(self, event: DetectionEvent):
        """Notify all observers about detection event"""
        for observer in self._observers:
            try:
                observer(event)
            except Exception as e:
                logger.error(f"Error in detection observer: {e}")

    def _notify_image_observers(self, image: MatLike):
        """Notify all image observers about processed image"""
        for observer in self._image_observers:
            try:
                observer(image)
            except Exception as e:
                logger.error(f"Error in image observer: {e}")

    @staticmethod
    def _classify_traffic_light(bbox: List[float]) -> TrafficLightColor:
        """Classify traffic light color based on bounding box position"""
        y_center = (bbox[1] + bbox[3]) / 2
        image_height = 640
        
        if y_center < image_height / 3:
            return TrafficLightColor.RED
        elif y_center < 2 * image_height / 3:
            return TrafficLightColor.YELLOW
        else:
            return TrafficLightColor.GREEN

    def _draw_bounding_boxes(self, image: MatLike, boxes: List[List[float]]) -> MatLike:
        """Draw bounding boxes on image"""
        image_copy = image.copy()
        
        for box in boxes:
            if len(box) >= 6:
                x1, y1, x2, y2, confidence, class_id = box[:6]
                
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                color = self._classify_traffic_light([x1, y1, x2, y2])
                rgb_color = color.color_rgb
                
                cv2.rectangle(image_copy, (x1, y1), (x2, y2), rgb_color, 2)
                
                label = f"{color.display_name} {confidence:.2f}"
                cv2.putText(image_copy, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, rgb_color, 2)
        
        return image_copy

    def predict(self, image: MatLike) -> List[list[float | int]]:
        """Predict bounding boxes in the image using YOLO"""
        results = self.model.predict(image)

        if results and results[0].boxes.data is not None:
            boxes = results[0].boxes.data.cpu().numpy().tolist()
            boxes = [[round(x, 2) for x in box] for box in boxes]
            
            timestamp = datetime.now()
            for box in boxes:
                if len(box) >= 6:
                    bbox = box[:4]
                    confidence = box[4]
                    color = self._classify_traffic_light(bbox)
                    
                    event = DetectionEvent(color, confidence, bbox, timestamp)
                    self._notify_observers(event)
            
            if boxes:
                image_with_boxes = self._draw_bounding_boxes(image, boxes)
                self._notify_image_observers(image_with_boxes)
            else:
                self._notify_image_observers(image)

            return boxes
        return []


detection_service = DetectionService()

import asyncio
import logging
import time
from typing import List, Callable, Optional, Awaitable

import cv2
from cv2.typing import MatLike
from ultralytics import YOLO

from chroma_ai.config.config import MODEL_PATH, BUFFERING_MULTIPLYER

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


class DetectionService:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self._interval_callback: Optional[Callable] = None
        self._log_observers: List[Callable[[str], None]] = []
        self._image_observers: List[Callable[[MatLike], None]] = []
        self._speed_observers: List[Callable[[float], None]] = []
        
        self._processing_times: List[float] = []
        self._last_processing_time: Optional[float] = None
        self._samples_count = 10
        self._last_interval_adjustment = 0

    def set_interval_callback(self, callback: Callable[[int], Awaitable[None]]):
        """Set callback for interval adjustments"""
        self._interval_callback = callback

    def add_log_observer(self, observer: Callable[[str], None]):
        """Add observer for detection events"""
        self._log_observers.append(observer)

    def remove_log_observer(self, observer: Callable[[str], None]):
        """Remove observer for detection events"""
        if observer in self._log_observers:
            self._log_observers.remove(observer)

    def add_image_observer(self, observer: Callable[[MatLike], None]):
        """Add observer for processed images with bounding boxes"""
        self._image_observers.append(observer)

    def remove_image_observer(self, observer: Callable[[MatLike], None]):
        """Remove observer for processed images"""
        if observer in self._image_observers:
            self._image_observers.remove(observer)

    def add_speed_observer(self, observer: Callable[[float], None]):
        """Add observer for processing speed updates"""
        self._speed_observers.append(observer)

    def remove_speed_observer(self, observer: Callable[[float], None]):
        """Remove observer for processing speed updates"""
        if observer in self._speed_observers:
            self._speed_observers.remove(observer)

    def _update_processing_stats(self, processing_time: float):
        """Update processing statistics and adjust interval if needed"""
        self._processing_times.append(processing_time)
        
        if len(self._processing_times) > self._samples_count:
            self._processing_times.pop(0)
        
        avg_processing_time = sum(self._processing_times) / len(self._processing_times)
        fps = 1.0 / avg_processing_time if avg_processing_time > 0 else 0
        
        for observer in self._speed_observers:
            try:
                observer(fps)
            except Exception as e:
                logger.error(f"Error in speed observer: {e}")
        
        if len(self._processing_times) >= self._samples_count:
            current_time = time.time()
            if current_time - self._last_interval_adjustment > 5:
                new_interval = max(40, int(avg_processing_time * 1000 * BUFFERING_MULTIPLYER))
                
                if self._interval_callback:
                    logger.info(f"Capture interval set to {new_interval} ms")
                    asyncio.create_task(self._interval_callback(new_interval))

                    self._notify_log_observers(f"Capture interval adjusted to {new_interval} ms")

                    self._last_interval_adjustment = current_time

    def _notify_log_observers(self, log: str):
        """Notify all observers about detection event"""
        for observer in self._log_observers:
            try:
                observer(log)
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
    def _draw_bounding_boxes(image: MatLike, boxes: List[List[int | float]]) -> MatLike:
        """Draw bounding boxes on image"""
        image_copy = image.copy()
        
        for box in boxes:
            if len(box) >= 6:
                x1, y1, x2, y2, confidence, class_id = box[:6]
                
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                color = [TrafficLightColor.GREEN, TrafficLightColor.RED, TrafficLightColor.YELLOW][int(class_id)]
                rgb_color = color.color_rgb
                
                cv2.rectangle(image_copy, (x1, y1), (x2, y2), rgb_color, 2)
                
                label = f"{color.display_name} {confidence:.2f}"
                cv2.putText(
                    image_copy,
                    label,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    rgb_color,
                    2
                )

        return image_copy

    def predict(self, image: MatLike) -> List[list[float | int]]:
        """Predict bounding boxes in the image using YOLO"""
        start_time = time.time()
        
        results = self.model.predict(image)
        
        processing_time = time.time() - start_time
        self._update_processing_stats(processing_time)

        if results and results[0].boxes.data is not None:
            boxes = results[0].boxes.data.cpu().numpy().tolist()
            boxes = [[round(x, 2) for x in box] for box in boxes]
            
            for box in boxes:
                if len(box) >= 6:
                    confidence = box[4]
                    class_id = int(box[5])
                    color = [TrafficLightColor.GREEN, TrafficLightColor.RED, TrafficLightColor.YELLOW][class_id]

                    self._notify_log_observers(f"{color} Detected | Conf: {confidence:.2f}")
            
            if boxes:
                image_with_boxes = self._draw_bounding_boxes(image, boxes)
                self._notify_image_observers(image_with_boxes)
            else:
                self._notify_image_observers(image)

            return boxes
        return []


detection_service = DetectionService()

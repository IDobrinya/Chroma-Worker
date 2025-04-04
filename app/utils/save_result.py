import os
from datetime import datetime

import cv2
from numpy import ndarray

from app.core.config import settings


async def save_result(image: ndarray, boxes: list | None):
    if not os.path.exists(settings.RESULTS_FOLDER):
        os.makedirs(settings.RESULTS_FOLDER)

    for box in boxes:
        if len(box) == 6:
            x1, y1, x2, y2, confidence, label = box
            if int(label) == 0:
                color = (0, 255, 0)
                label_text = "GREEN"
            elif int(label) == 1:
                color = (0, 0, 255)
                label_text = "RED"
            elif int(label) == 2:
                color = (0, 255, 255)
                label_text = "YELLOW"
            else:
                color = (255, 255, 255)
                label_text = "UNKNOWN"
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 3)
            text = f"{label_text} {confidence:.2f}"
            cv2.putText(image, text, (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = os.path.join(settings.RESULTS_FOLDER, f"result_{timestamp}.jpeg")
    cv2.imwrite(filename, image)

import numpy as np
import logging
from loguru import logger

from app.core.config import settings
from ultralytics import YOLO

PUBLIC_KEY = None

if settings.JWT_VERIFICATION:
    with open(settings.PUBLISHABLE_KEY_PATH, 'r') as file:
        PUBLIC_KEY = file.read()

logger.info(f"Initializing YOLO model from {settings.MODEL_PATH}")
model = YOLO(settings.MODEL_PATH)
logging.getLogger("ultralytics").setLevel(logging.WARNING)
model.predict(np.zeros((1, 1, 3), dtype=np.uint8))
logging.getLogger("ultralytics").setLevel(logging.INFO)
logger.info("Model initialized")

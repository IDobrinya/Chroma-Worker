import json
import logging

import numpy as np
import cv2
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from starlette import status

from src.chroma_ai.services.yolo_service import yolo_service

logger = logging.getLogger(__name__)

ws_router = APIRouter()
connection = None


@ws_router.websocket("/")
async def ws(websocket: WebSocket):
    global connection

    if connection is not None:
        logger.warning("Policy violation: another connection is already active")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Only one active connection is allowed."
        )
        return

    connection = websocket
    await websocket.accept()
    try:
        await websocket.receive_text()

        logger.info("Client connected successfully")

        while True:
            frame_bytes = await websocket.receive_bytes()

            image_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                logger.error("Received invalid image data")
                continue

            boxes = yolo_service.predict(image)
            await websocket.send_text(json.dumps(boxes))

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        connection = None

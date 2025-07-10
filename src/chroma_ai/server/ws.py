import json
import logging

import numpy as np
import cv2
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from starlette import status

from src.chroma_ai.services.detection_service import detection_service
from src.chroma_ai.services.connection_manager import connection_manager

logger = logging.getLogger(__name__)

ws_router = APIRouter()


@ws_router.websocket("/")
async def ws(websocket: WebSocket):
    if connection_manager.is_connected():
        logger.warning("Policy violation: another connection is already active")
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Only one active connection is allowed."
        )
        return

    await websocket.accept()
    connection_manager.set_connected()

    async def callback(interval):
        await websocket.send_text(json.dumps({"type": "set_interval", "interval": interval}))

    detection_service.set_interval_callback(
        callback
    )

    await websocket.send_text(json.dumps({"status": "success"}))
    logger.info("Client connected successfully")

    try:
        while True:
            frame_bytes = await websocket.receive_bytes()

            image_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if image is None:
                logger.error("Received invalid image data")
                continue

            boxes = detection_service.predict(image)
            await websocket.send_text(json.dumps(boxes))

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
    finally:
        connection_manager.set_disconnected()

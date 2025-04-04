import json

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from loguru import logger

from app.core.config import settings
from app.core.loader import model
from app.utils.verify_token import verify_token

from app.utils.save_result import save_result

app = FastAPI(title=settings.PROJECT)

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        if settings.JWT_VERIFICATION:
            token_data = json.loads(data)
            token_encoded = token_data.get("token")
            status, message, user_id = await verify_token(token_encoded)

            await websocket.send_text(json.dumps({"status": status, "message": message}))

            if status == "error":
                logger.warning("Token validation not passed")
                await websocket.close()
                return
            logger.info(f"Client connected successfully | user_id: {user_id}")
        else:
            logger.info("Client connected successfully")

        while True:
            frame_bytes = await websocket.receive_bytes()

            image_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            results = model.predict(image)

            if results and results[0].boxes.data is not None:
                boxes = results[0].boxes.data.cpu().numpy().tolist()
            else:
                boxes = []
            boxes = [[round(x, 2) for x in box] for box in boxes]

            if boxes:
                filter_label = boxes[0][5]
                boxes = list(filter(lambda b: b[5] == filter_label, boxes))

            await websocket.send_text(json.dumps(boxes))

            if settings.SAVE_RESULTS:
                await save_result(image, boxes)

    except WebSocketDisconnect:
        logger.error("WebSocket disconnected")

if __name__ == "__main__":
    logger.info("Chroma-Worker startup")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

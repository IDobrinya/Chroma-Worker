from fastapi import FastAPI, WebSocket, Request
from loguru import logger
import uvicorn

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import asyncio

from app.core.config import settings
from app.utils.auth import verify_token

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
            logger.info(f"Client connected successfully")

        while True:
            frame = await websocket.receive_bytes()
            logger.debug("Received frame")
            result = [[10.0, 20.0, 300.0, 400.0, 0.95, 1]]
            await websocket.send_text(json.dumps(result))
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.error("WebSocket disconnected")


if __name__ == "__main__":
    logger.info("Chroma-Worker startup")

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)

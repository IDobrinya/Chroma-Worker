from fastapi import FastAPI, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/Auth")
async def auth_check(request: Request):
    headers = request.headers
    logger.info(f"Headers: {headers}")
    return {
        "status": "success",
        "message": "Authenticated",
        "headers": dict(headers)
    }


@app.websocket("/")
async def predict(
        websocket: WebSocket,
):
    headers = websocket.headers
    logger.info(f"headers: {headers}")
    await websocket.accept()


uvicorn.run(app, host="localhost", port=8000)

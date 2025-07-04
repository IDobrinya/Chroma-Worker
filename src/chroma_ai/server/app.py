import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.chroma_ai.server.ws import ws_router

app = FastAPI()

app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

app.include_router(ws_router)

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

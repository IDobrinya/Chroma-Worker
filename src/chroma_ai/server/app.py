import uvicorn
import logging
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

# noinspection PyUnresolvedReferences
from chroma_ai.config import logging as logging_cfg
from chroma_ai.server.ws import ws_router

app = FastAPI()

app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

app.include_router(ws_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is running"}


def run_server(port):
    logger = logging.getLogger("uvicorn")
    logger.info(f"Starting server on port {port}")

    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        log_level="error",
        access_log=True
    )
    
    return port

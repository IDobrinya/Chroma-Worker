import threading
import logging

from src.chroma_ai.services.app_manager import app_manager
from src.chroma_ai.ui.app import ChromaAIGui
from src.chroma_ai.auth.instance_token import token_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Chroma AI Client")

    logger.info("Registering server")
    token_manager.register_server()

    gui = ChromaAIGui()

    logger.info("Starting services in background")
    threading.Thread(target=app_manager.start_services, daemon=True).start()

    logger.info("Starting GUI")
    gui.run()

if __name__ == "__main__":
    main()

import logging

from src.chroma_ai.services.app_manager import app_manager
from src.chroma_ai.ui.app import ChromaAIGui

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    logger.info("Starting Chroma AI Client")

    logger.info("Starting services")
    app_manager.start_services()

    logger.info("Starting GUI")
    gui = ChromaAIGui()
    gui.run()


if __name__ == "__main__":
    main()

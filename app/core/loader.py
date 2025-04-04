from loguru import logger

from app.core.config import settings


PUBLIC_KEY = None

if settings.JWT_VERIFICATION:
    try:
        with open(settings.PUBLISHABLE_KEY_PATH, 'r') as file:
            PUBLIC_KEY = file.read()
    except FileNotFoundError:
        logger.error(f"Public key file not found at {settings.JWT_PUBLIC_KEY_PATH}")
    except Exception as e:
        logger.error(f"Error loading public key: {e}")
        PUBLIC_KEY = None

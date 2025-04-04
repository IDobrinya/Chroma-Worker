import jwt
from loguru import logger

from app.core.config import settings
from app.core.loader import PUBLIC_KEY


async def verify_token(token: str) -> (str, str, str):
    payload = {}
    try:
        logger.debug(token)
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return "success", "Token accepted",  payload.get("user_id")
    except jwt.exceptions.ExpiredSignatureError:
        logger.warning("Token expired")
        return "error", "Expired token", payload.get("user_id")
    except jwt.exceptions.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return "error", "Invalid token", payload.get("user_id")
    except Exception as e:
        logger.error(f"Unexpected error validating token: {e}")
        return "error", "Token validation error", payload.get("user_id")

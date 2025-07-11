
import json
import secrets
import string
from pathlib import Path
import logging
import requests
from chroma_ai.config.config import SERVER_API_BASE

from appdirs import user_config_dir

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Generates token stored in the user config directory.
    """
    def __init__(self, app_name: str = "ChromaAI"):
        cfg_dir = Path(user_config_dir(app_name))
        cfg_dir.mkdir(parents=True, exist_ok=True)
        self._path = cfg_dir / "credentials.json"

    def get_token(self) -> str:
        if not self._path.exists():
            token = "sk-" + "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            self._path.write_text(json.dumps({"token": token}), encoding="utf-8")

            return token

        data = json.loads(self._path.read_text(encoding="utf-8"))
        return data["token"]

    def register_server(self) -> bool:
        """Register server using token"""
        try:
            token = self.get_token()
            url = f"{SERVER_API_BASE}/servers/register"
            
            payload = {
                "token": token
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully registered server with central server")
                return True
            else:
                logger.warning(f"Failed to register server: {response.status_code} - {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error registering server: {e}")
            return False


token_manager = TokenManager()

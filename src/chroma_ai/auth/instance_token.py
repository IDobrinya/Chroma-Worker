
import json
import secrets
import string
from pathlib import Path

from appdirs import user_config_dir


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


token_manager = TokenManager()

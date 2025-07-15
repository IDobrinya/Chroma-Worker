import sys
from pathlib import Path

def resource_path(relative_path):
    base_path = getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3])
    return Path(base_path) / relative_path

ASSETS_DIR = resource_path("assets")
CLOUDFLARED_PATH = ASSETS_DIR / "cloudflared" / "cloudflared.exe"
MODEL_PATH = ASSETS_DIR / "models" / "chroma-default.pt"
ICON_PATH = ASSETS_DIR / "media" / "icon.png"

WEB_CLIENT_URL = "https://chroma-ai-weld.vercel.app"

SERVER_URL = "https://serverregistry-eu-west.up.railway.app"
SERVER_API_BASE = f"{SERVER_URL}/api/v1"

BUFFERING_MULTIPLYER = 1.2

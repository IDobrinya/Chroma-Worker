from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets"
CLOUDFLARED_PATH = ASSETS_DIR / "cloudflared" / "cloudflared.exe"
MODEL_PATH = ASSETS_DIR / "models" / "chroma-default.pt"

WEB_CLIENT_URL = "https://chroma-ai-weld.vercel.app/"

SERVER_URL = "http://localhost:8080"
SERVER_API_BASE = f"{SERVER_URL}/api/v1"

BUFFERING_MULTIPLYER = 1.2

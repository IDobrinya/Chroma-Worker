from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets"
CLOUDFLARED_PATH = ASSETS_DIR / "cloudflared" / "cloudflared.exe"
MODEL_PATH = ASSETS_DIR / "models" / "chroma-default.pt"

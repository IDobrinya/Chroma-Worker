import logging
import sys
from pathlib import Path

from appdirs import user_config_dir

cfg_dir = Path(user_config_dir("ChromaAI"))
cfg_dir.mkdir(parents=True, exist_ok=True)
log_file = cfg_dir / "logs.log"
cloudflared_log_file = cfg_dir / "cloudflared.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logging.getLogger("ultralytics").setLevel(logging.WARNING)

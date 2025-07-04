import re
import signal
import subprocess
import time
from typing import Optional

from src.chroma_ai.config.config import CLOUDFLARED_PATH


class TunnelManager:
    def __init__(self, port: int):
        """
        Initialize tunnel manager

        Args:
            port: Local port to expose through the tunnel
        """
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None

        self.cloudflared_path = CLOUDFLARED_PATH

        if not self.cloudflared_path.exists():
            raise FileNotFoundError(f"cloudflared binary not found at {self.cloudflared_path}")

    def start(self) -> str:
        """
        Start the tunnel and return the public URL

        Returns:
            str: Public tunnel URL

        Raises:
            RuntimeError: If tunnel fails to start or URL cannot be parsed
        """
        if self.process:
            return self.tunnel_url if self.tunnel_url else ""

        # Command to start cloudflared tunnel
        cmd = [
            str(self.cloudflared_path),
            "tunnel",
            "--url",
            f"wss://localhost:{self.port}"
        ]

        # Start cloudflared process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Wait for tunnel URL to appear in output
        start_time = time.time()
        while time.time() - start_time < 15:
            if not self.process.stdout:
                continue

            line = self.process.stdout.readline()
            if not line:
                continue

            url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if url_match:
                self.tunnel_url = url_match.group(0)
                return self.tunnel_url

            time.sleep(0.5)

        raise RuntimeError("Timeout waiting for tunnel URL")

    def stop(self) -> None:
        """Stop the tunnel if it's running"""
        if self.process:
            self.process.send_signal(signal.CTRL_BREAK_EVENT)

            self.process.wait()
            self.process = None
            self.tunnel_url = None

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.stop()

    @property
    def is_running(self) -> bool:
        """Check if tunnel is currently running"""
        return self.process is not None and self.process.poll() is None


if __name__ == "__main__":
    with TunnelManager(80) as tunnel:
        url = tunnel.tunnel_url
        print(url)

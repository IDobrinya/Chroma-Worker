import logging
import re
import subprocess
import time
from typing import Optional
import requests

from chroma_ai.config.config import CLOUDFLARED_PATH, SERVER_API_BASE
from chroma_ai.auth.instance_token import token_manager

logger = logging.getLogger(__name__)


class TunnelManager:
    def __init__(self):
        """
        Initialize tunnel manager
        """
        self.port = 8000
        self.process: Optional[subprocess.Popen] = None
        self.tunnel_url: Optional[str] = None

        self.cloudflared_path = CLOUDFLARED_PATH

        if not self.cloudflared_path.exists():
            raise FileNotFoundError(f"cloudflared binary not found at {self.cloudflared_path}")

    def start(self, port: int) -> str:
        """
        Start the tunnel and return the public URL

        Returns:
            str: Public tunnel URL

        Raises:
            RuntimeError: If tunnel fails to start or URL cannot be parsed
        """
        self.port = port
        if self.process:
            return self.tunnel_url if self.tunnel_url else ""

        # Command to start cloudflared tunnel
        cmd = [
            str(self.cloudflared_path),
            "tunnel",
            "--url",
            f"http://localhost:{self.port}"
        ]

        # Start cloudflared process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        start_time = time.time()
        while time.time() - start_time < 15:
            if not self.process.stdout:
                continue

            line = self.process.stdout.readline()
            if not line:
                continue

            url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if url_match:
                self.tunnel_url = url_match.group(0).replace("https", "wss")
                logger.info(f"Tunnel URL: {self.tunnel_url}")
                
                self._register_tunnel_url()
                
                return self.tunnel_url

            time.sleep(0.5)

        raise RuntimeError("Timeout waiting for tunnel URL")

    def stop(self) -> None:
        """Stop the tunnel if it's running"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            
            self.process = None
            self.tunnel_url = None

    def _register_tunnel_url(self) -> None:
        """Register tunnel URL with central server"""
        if not self.tunnel_url:
            return
        
        try:
            token = token_manager.get_token()
            url = f"{SERVER_API_BASE}/servers/tunnel"
            
            payload = {
                "token": token,
                "bridge_url": self.tunnel_url
            }
            
            response = requests.put(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Successfully registered tunnel URL with central server")
            else:
                logger.warning(f"Failed to register tunnel URL: {response.status_code} - {response.text}")
        
        except Exception as e:
            logger.error(f"Error registering tunnel URL: {e}")

    @property
    def is_running(self) -> bool:
        """Check if tunnel is currently running"""
        return self.process is not None and self.process.poll() is None


tunnel_manager = TunnelManager()

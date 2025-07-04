import logging
import sys
import threading
import time
from enum import Enum
from typing import Optional

from src.chroma_ai.auth.instance_token import token_manager
from src.chroma_ai.server.app import run_server
from src.chroma_ai.services.connection_manager import connection_manager
from src.chroma_ai.services.tunnel_service import tunnel_manager

logger = logging.getLogger(__name__)


class ApplicationState(Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AppManager:
    _lock = threading.Lock()

    def __init__(self):
        self._state = ApplicationState.INITIALIZING
        self._server_thread: Optional[threading.Thread] = None
        self._tunnel_url: Optional[str] = None
        self._lock = threading.Lock()

        self.token = token_manager.get_token()
        logger.info(f"Application initialized with token: {self.token[:8]}...")

    def _set_state(self, state: ApplicationState):
        """Set application state and notify observers"""
        with self._lock:
            if self._state != state:
                old_state = self._state
                self._state = state
                logger.info(f"Application state changed: {old_state.value} -> {state.value}")

    def get_state(self) -> ApplicationState:
        """Get current application state"""
        with self._lock:
            return self._state

    def get_tunnel_url(self) -> Optional[str]:
        """Get tunnel URL"""
        with self._lock:
            return self._tunnel_url

    def start_services(self):
        """Start server and tunnel services"""
        self._set_state(ApplicationState.STARTING)

        try:
            self._server_thread = threading.Thread(target=run_server, daemon=True)
            self._server_thread.start()

            self._tunnel_url = tunnel_manager.start(8000)

            self._set_state(ApplicationState.RUNNING)

        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            self._set_state(ApplicationState.ERROR)
            raise

    def stop_services(self):
        """Stop all services"""
        self._set_state(ApplicationState.STOPPING)

        try:
            logger.info("Stopping tunnel...")
            tunnel_manager.stop()

            logger.info("Disconnecting clients...")
            connection_manager.set_disconnected()

            self._tunnel_url = None
            self._set_state(ApplicationState.STOPPED)
            logger.info("All services stopped")

        except Exception as e:
            logger.error(f"Error stopping services: {e}")

    def shutdown(self):
        """Graceful shutdown of entire application"""
        logger.info("Initiating application shutdown...")
        self.stop_services()

        time.sleep(1)

        logger.info("Application shutdown complete")
        sys.exit(0)


app_manager = AppManager()

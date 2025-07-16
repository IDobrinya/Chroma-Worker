import logging
import socket
import sys
import threading
import time
from enum import Enum
from typing import Optional, Callable

from chroma_ai.auth.instance_token import token_manager
from chroma_ai.server.app import run_server
from chroma_ai.services.connection_manager import connection_manager, ConnectionState
from chroma_ai.services.tunnel_service import tunnel_manager

logger = logging.getLogger(__name__)


class ApplicationState(Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    WAITING = "waiting"
    CONNECTED = "connected"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class AppManager:
    def __init__(self):
        self._state = ApplicationState.INITIALIZING
        self._server_thread: Optional[threading.Thread] = None
        self._tunnel_url: Optional[str] = None
        self._observers: list[Callable] = []
        self._lock = threading.Lock()
        self._port: Optional[int] = None

        self.token = token_manager.get_token()
        logger.info(f"Application initialized with token: {self.token[:8]}...")

    def add_observer(self, callback: Callable):
        if callback not in self._observers:
            self._observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self):
        for callback in self._observers:
            try:
                callback(self._state)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")

    def _set_state(self, state: ApplicationState):
        if self._state != state:
            old_state = self._state
            self._state = state
            logger.info(f"Application state changed: {old_state.value} -> {state.value}")
            self._notify_observers()

    def on_connection_state_changed(self, state: ConnectionState):
        if state == ConnectionState.CONNECTED:
            self._set_state(ApplicationState.CONNECTED)
        else:
            self._set_state(ApplicationState.WAITING)

    def get_state(self) -> ApplicationState:
        """Get current application state"""
        return self._state

    def get_tunnel_url(self) -> Optional[str]:
        """Get tunnel URL"""
        return self._tunnel_url

    def start_services(self):
        """Start server and tunnel services"""
        self._set_state(ApplicationState.STARTING)

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', 0))
                s.listen(1)
                self._port = s.getsockname()[1]

            threading.Thread(target=run_server, args=(self._port,), daemon=True).start()
            self._tunnel_url = tunnel_manager.start(self._port)

            connection_manager.add_observer(self.on_connection_state_changed)
            self._set_state(ApplicationState.WAITING)

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

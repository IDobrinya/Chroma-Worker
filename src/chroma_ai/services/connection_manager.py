import time
from enum import Enum
from typing import Optional, Callable

from starlette.websockets import WebSocket


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


class ConnectionManager:
    def __init__(self):
        self._initialized = True
        self._state = ConnectionState.DISCONNECTED
        self._connection_start_time: Optional[float] = None
        self._observers: list[Callable] = []

    def add_observer(self, callback: Callable):
        """Add observer for connection state changes"""
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback: Callable):
        """Remove observer for connection state changes"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self):
        """Notify all observers about state change"""
        for callback in self._observers:
            try:
                callback(self._state)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def set_connected(self):
        """Set connection state to connected"""
        if self._state != ConnectionState.CONNECTED:
            self._state = ConnectionState.CONNECTED
            self._connection_start_time = time.time()
            self._notify_observers()

    def set_disconnected(self):
        """Set connection state to disconnected"""
        if self._state != ConnectionState.DISCONNECTED:
            self._state = ConnectionState.DISCONNECTED
            self._connection_start_time = None
            self._notify_observers()

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self._state == ConnectionState.CONNECTED

    def get_connection_time(self) -> Optional[float]:
        """Get connection start time"""
        return self._connection_start_time

    def get_state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state


connection_manager = ConnectionManager()

import threading
import time
from typing import Optional, Callable
from enum import Enum

from starlette.websockets import WebSocket


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"


class ConnectionManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._connection = None
        self._state = ConnectionState.DISCONNECTED
        self._connection_start_time: Optional[float] = None
        self._observers: list[Callable] = []
        self._lock = threading.Lock()
    
    def add_observer(self, callback: Callable):
        """Add observer for connection state changes"""
        with self._lock:
            if callback not in self._observers:
                self._observers.append(callback)
    
    def remove_observer(self, callback: Callable):
        """Remove observer for connection state changes"""
        with self._lock:
            if callback in self._observers:
                self._observers.remove(callback)
    
    def _notify_observers(self):
        """Notify all observers about state change"""
        with self._lock:
            for callback in self._observers:
                try:
                    callback(self._state)
                except Exception as e:
                    print(f"Error notifying observer: {e}")
    
    def set_connected(self, websocket: WebSocket):
        """Set connection state to connected"""
        with self._lock:
            if self._state != ConnectionState.CONNECTED:
                self._connection = websocket
                self._state = ConnectionState.CONNECTED
                self._connection_start_time = time.time()
                self._notify_observers()
    
    def set_disconnected(self):
        """Set connection state to disconnected"""
        with self._lock:
            if self._state != ConnectionState.DISCONNECTED:
                self._connection.close(code=1001, reason="Connection closed by server.")
                self._connection = None
                self._state = ConnectionState.DISCONNECTED
                self._connection_start_time = None
                self._notify_observers()
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        with self._lock:
            return self._state == ConnectionState.CONNECTED
    
    def get_connection_time(self) -> Optional[float]:
        """Get connection start time"""
        with self._lock:
            return self._connection_start_time
    
    def get_state(self) -> ConnectionState:
        """Get current connection state"""
        with self._lock:
            return self._state


connection_manager = ConnectionManager()
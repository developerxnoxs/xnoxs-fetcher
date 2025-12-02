"""
XnoxsFetcher WebSocket Manager Module

This module provides robust WebSocket connection management with
automatic reconnection, heartbeat, and connection state tracking.

Author: developerxnoxs
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Any, List

from websocket import create_connection, WebSocket, WebSocketException

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


@dataclass
class WebSocketConfig:
    """Configuration for WebSocket manager."""
    endpoint: str = "wss://data.tradingview.com/socket.io/websocket"
    origin: str = "https://data.tradingview.com"
    timeout: int = 5
    heartbeat_interval: int = 10
    max_reconnect_attempts: int = 5
    reconnect_delay: float = 1.0
    reconnect_delay_max: float = 30.0
    ping_timeout: int = 30


class WebSocketManager:
    """
    Robust WebSocket Connection Manager.
    
    Features:
        - Automatic reconnection with exponential backoff
        - Heartbeat/ping mechanism
        - Connection state tracking
        - Thread-safe operations
        - Event callbacks for state changes
    
    Example:
        >>> ws_manager = WebSocketManager()
        >>> ws_manager.connect()
        >>> ws_manager.send_message("set_auth_token", ["token"])
        >>> response = ws_manager.receive()
    
    Author: developerxnoxs
    """
    
    def __init__(
        self, 
        config: Optional[WebSocketConfig] = None,
        on_state_change: Optional[Callable[[ConnectionState], None]] = None,
        on_message: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None
    ):
        """
        Initialize WebSocketManager.
        
        Args:
            config: WebSocket configuration
            on_state_change: Callback for connection state changes
            on_message: Callback for received messages
            on_error: Callback for errors
        """
        self._config = config or WebSocketConfig()
        self._ws: Optional[WebSocket] = None
        self._state = ConnectionState.DISCONNECTED
        self._lock = threading.Lock()
        self._reconnect_count = 0
        self._last_pong = time.time()
        
        self._on_state_change = on_state_change
        self._on_message = on_message
        self._on_error = on_error
        
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._stop_heartbeat = threading.Event()
        
        self._message_buffer: List[str] = []
    
    @property
    def state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self._state == ConnectionState.CONNECTED
    
    def _set_state(self, new_state: ConnectionState) -> None:
        """Update connection state and notify callback."""
        old_state = self._state
        self._state = new_state
        
        if old_state != new_state:
            logger.info(f"WebSocket state: {old_state.value} -> {new_state.value}")
            if self._on_state_change:
                try:
                    self._on_state_change(new_state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")
    
    def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            True if connected successfully
        """
        with self._lock:
            if self._state == ConnectionState.CONNECTED:
                return True
            
            self._set_state(ConnectionState.CONNECTING)
            
            try:
                self._ws = create_connection(
                    self._config.endpoint,
                    origin=self._config.origin,
                    timeout=self._config.timeout
                )
                
                self._set_state(ConnectionState.CONNECTED)
                self._reconnect_count = 0
                self._last_pong = time.time()
                
                self._start_heartbeat()
                
                logger.info("WebSocket connected successfully")
                return True
                
            except Exception as e:
                logger.error(f"WebSocket connection failed: {e}")
                self._set_state(ConnectionState.DISCONNECTED)
                
                if self._on_error:
                    self._on_error(e)
                
                return False
    
    def disconnect(self) -> None:
        """Close WebSocket connection."""
        with self._lock:
            self._stop_heartbeat.set()
            
            if self._ws:
                try:
                    self._ws.close()
                except Exception:
                    pass
                self._ws = None
            
            self._set_state(ConnectionState.CLOSED)
            logger.info("WebSocket disconnected")
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Returns:
            True if reconnected successfully
        """
        if self._state == ConnectionState.CLOSED:
            logger.warning("Cannot reconnect - connection was explicitly closed")
            return False
        
        self._set_state(ConnectionState.RECONNECTING)
        
        for attempt in range(self._config.max_reconnect_attempts):
            self._reconnect_count = attempt + 1
            
            delay = min(
                self._config.reconnect_delay * (2 ** attempt),
                self._config.reconnect_delay_max
            )
            
            logger.info(
                f"Reconnect attempt {self._reconnect_count}/"
                f"{self._config.max_reconnect_attempts} in {delay:.1f}s"
            )
            
            time.sleep(delay)
            
            if self._ws:
                try:
                    self._ws.close()
                except Exception:
                    pass
                self._ws = None
            
            if self.connect():
                logger.info("Reconnected successfully")
                return True
        
        logger.error("Failed to reconnect after all attempts")
        self._set_state(ConnectionState.DISCONNECTED)
        return False
    
    def _start_heartbeat(self) -> None:
        """Start heartbeat thread."""
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        
        self._stop_heartbeat.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="ws_heartbeat"
        )
        self._heartbeat_thread.start()
    
    def _heartbeat_loop(self) -> None:
        """Heartbeat loop to keep connection alive."""
        while not self._stop_heartbeat.is_set():
            if self._state != ConnectionState.CONNECTED:
                break
            
            if time.time() - self._last_pong > self._config.ping_timeout:
                logger.warning("Ping timeout - attempting reconnect")
                self.reconnect()
                break
            
            try:
                if self._ws:
                    self._ws.ping()
            except Exception as e:
                logger.warning(f"Ping failed: {e}")
            
            self._stop_heartbeat.wait(timeout=self._config.heartbeat_interval)
    
    def send(self, message: str) -> bool:
        """
        Send raw message through WebSocket.
        
        Args:
            message: Message string to send
            
        Returns:
            True if sent successfully
        """
        if not self.is_connected or self._ws is None:
            if not self.reconnect():
                return False
        
        try:
            self._ws.send(message)
            return True
        except WebSocketException as e:
            logger.error(f"Send failed: {e}")
            if self._on_error:
                self._on_error(e)
            return False
    
    def send_message(self, func_name: str, params: List[Any]) -> bool:
        """
        Send formatted TradingView message.
        
        Args:
            func_name: Function name
            params: Parameters list
            
        Returns:
            True if sent successfully
        """
        message = self._build_message(func_name, params)
        formatted = self._add_header(message)
        return self.send(formatted)
    
    @staticmethod
    def _add_header(message: str) -> str:
        """Add TradingView message header."""
        return f"~m~{len(message)}~m~{message}"
    
    @staticmethod
    def _build_message(func_name: str, params: List[Any]) -> str:
        """Build JSON message for WebSocket."""
        return json.dumps({"m": func_name, "p": params}, separators=(",", ":"))
    
    def receive(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Receive message from WebSocket.
        
        Args:
            timeout: Receive timeout in seconds
            
        Returns:
            Received message or None
        """
        if not self.is_connected or self._ws is None:
            if not self.reconnect():
                return None
        
        try:
            if timeout:
                self._ws.settimeout(timeout)
            
            result = self._ws.recv()
            self._last_pong = time.time()
            
            if self._on_message:
                self._on_message(result)
            
            return result
            
        except WebSocketException as e:
            logger.error(f"Receive failed: {e}")
            if self._on_error:
                self._on_error(e)
            return None
    
    def receive_until(
        self, 
        stop_condition: str,
        timeout: float = 60.0
    ) -> str:
        """
        Receive messages until stop condition is met.
        
        Args:
            stop_condition: String to look for in messages
            timeout: Maximum wait time
            
        Returns:
            Concatenated received messages
        """
        raw_data = ""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                logger.warning("Receive timeout reached")
                break
            
            try:
                result = self.receive(timeout=5.0)
                if result:
                    raw_data += result + "\n"
                    
                    if stop_condition in result:
                        break
            except Exception as e:
                logger.error(f"Receive error: {e}")
                break
        
        return raw_data
    
    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "state": self._state.value,
            "reconnect_count": self._reconnect_count,
            "last_pong_seconds_ago": time.time() - self._last_pong,
            "is_connected": self.is_connected
        }


class WebSocketPool:
    """
    Pool of WebSocket connections for parallel operations.
    
    Manages multiple WebSocket connections for concurrent
    data fetching operations.
    """
    
    def __init__(
        self, 
        pool_size: int = 3,
        config: Optional[WebSocketConfig] = None
    ):
        """
        Initialize WebSocket pool.
        
        Args:
            pool_size: Number of connections in pool
            config: WebSocket configuration
        """
        self._pool_size = pool_size
        self._config = config or WebSocketConfig()
        self._connections: List[WebSocketManager] = []
        self._available: List[WebSocketManager] = []
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
    
    def initialize(self) -> None:
        """Initialize all connections in pool."""
        for _ in range(self._pool_size):
            ws = WebSocketManager(config=self._config)
            ws.connect()
            self._connections.append(ws)
            self._available.append(ws)
    
    def acquire(self, timeout: float = 30.0) -> Optional[WebSocketManager]:
        """
        Acquire a connection from the pool.
        
        Args:
            timeout: Maximum wait time
            
        Returns:
            WebSocketManager or None if timeout
        """
        with self._condition:
            start = time.time()
            
            while not self._available:
                remaining = timeout - (time.time() - start)
                if remaining <= 0:
                    return None
                self._condition.wait(timeout=remaining)
            
            return self._available.pop()
    
    def release(self, ws: WebSocketManager) -> None:
        """
        Release connection back to pool.
        
        Args:
            ws: WebSocketManager to release
        """
        with self._condition:
            if ws in self._connections:
                self._available.append(ws)
                self._condition.notify()
    
    def shutdown(self) -> None:
        """Close all connections in pool."""
        with self._lock:
            for ws in self._connections:
                ws.disconnect()
            self._connections.clear()
            self._available.clear()

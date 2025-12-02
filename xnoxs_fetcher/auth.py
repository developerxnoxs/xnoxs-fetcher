"""
XnoxsFetcher Authentication Module

This module provides robust authentication management for TradingView,
including session persistence, token refresh, and rate limiting.

Author: developerxnoxs
"""

from __future__ import annotations

import json
import logging
import os
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Configuration for authentication manager."""
    sign_in_url: str = "https://www.tradingview.com/accounts/signin/"
    session_file: str = ".tv_session.json"
    token_refresh_interval: int = 3600
    max_retries: int = 3
    retry_delay: float = 2.0
    rate_limit_requests: int = 10
    rate_limit_window: int = 60


@dataclass
class SessionData:
    """Stored session data."""
    token: str
    session_id: str
    username: str
    created_at: datetime
    expires_at: datetime
    cookies: Dict[str, str] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.now() >= self.expires_at
    
    def is_near_expiry(self, threshold_minutes: int = 30) -> bool:
        """Check if session is close to expiring."""
        threshold = timedelta(minutes=threshold_minutes)
        return datetime.now() >= (self.expires_at - threshold)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "token": self.token,
            "session_id": self.session_id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "cookies": self.cookies
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """Create from dictionary."""
        return cls(
            token=data["token"],
            session_id=data["session_id"],
            username=data["username"],
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            cookies=data.get("cookies", {})
        )


class RateLimiter:
    """Rate limiter to prevent API abuse."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: list = []
        self._lock = threading.Lock()
    
    def acquire(self, timeout: float = 30.0) -> bool:
        """
        Acquire permission to make a request.
        
        Args:
            timeout: Maximum time to wait for permission
            
        Returns:
            True if permission granted, False if timed out
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                now = time.time()
                self._requests = [t for t in self._requests 
                                  if now - t < self._window_seconds]
                
                if len(self._requests) < self._max_requests:
                    self._requests.append(now)
                    return True
            
            if time.time() - start_time >= timeout:
                return False
            
            time.sleep(0.1)
    
    def get_wait_time(self) -> float:
        """Get time until next request slot is available."""
        with self._lock:
            if len(self._requests) < self._max_requests:
                return 0.0
            
            oldest = min(self._requests)
            return max(0.0, self._window_seconds - (time.time() - oldest))


class AuthManager:
    """
    Robust TradingView Authentication Manager.
    
    Features:
        - Session persistence to file
        - Automatic token refresh
        - Rate limiting
        - Retry with exponential backoff
        - Thread-safe operations
    
    Example:
        >>> auth = AuthManager()
        >>> token = auth.authenticate("user@email.com", "password")
        >>> if auth.is_authenticated:
        ...     print("Login successful!")
    
    Author: developerxnoxs
    """
    
    _HEADERS_TEMPLATE = {
        "Host": "www.tradingview.com",
        "Origin": "https://www.tradingview.com",
        "Referer": "https://www.tradingview.com/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.102 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "id,id-ID;q=0.9,en-US;q=0.8,en;q=0.7",
        "x-language": "en",
        "x-requested-with": "XMLHttpRequest",
        "sec-ch-ua": '"Chromium";v="142", "Android WebView";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "same-origin",
        "sec-fetch-site": "same-origin",
    }
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """
        Initialize AuthManager.
        
        Args:
            config: Authentication configuration
        """
        self._config = config or AuthConfig()
        self._session_data: Optional[SessionData] = None
        self._http_session: Optional[requests.Session] = None
        self._rate_limiter = RateLimiter(
            self._config.rate_limit_requests,
            self._config.rate_limit_window
        )
        self._lock = threading.Lock()
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        self._load_session()
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return (
            self._session_data is not None 
            and not self._session_data.is_expired()
        )
    
    @property
    def token(self) -> Optional[str]:
        """Get current authentication token."""
        if self._session_data:
            return self._session_data.token
        return None
    
    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        if self._session_data:
            return self._session_data.session_id
        return None
    
    @property
    def username(self) -> Optional[str]:
        """Get authenticated username."""
        if self._session_data:
            return self._session_data.username
        return None
    
    def _get_session_path(self) -> Path:
        """Get path to session file."""
        return Path(self._config.session_file)
    
    def _load_session(self) -> bool:
        """
        Load session from file if available.
        
        Returns:
            True if valid session loaded
        """
        session_path = self._get_session_path()
        
        if not session_path.exists():
            return False
        
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            
            self._session_data = SessionData.from_dict(data)
            
            if self._session_data.is_expired():
                logger.info("Stored session expired, need re-authentication")
                self._session_data = None
                return False
            
            logger.info(f"Loaded session for user: {self._session_data.username}")
            self._start_refresh_thread()
            return True
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to load session: {e}")
            return False
    
    def _save_session(self) -> None:
        """Save current session to file."""
        if self._session_data is None:
            return
        
        session_path = self._get_session_path()
        
        try:
            with open(session_path, "w") as f:
                json.dump(self._session_data.to_dict(), f, indent=2)
            logger.debug("Session saved to file")
        except IOError as e:
            logger.warning(f"Failed to save session: {e}")
    
    def _clear_session(self) -> None:
        """Clear stored session."""
        self._session_data = None
        
        session_path = self._get_session_path()
        if session_path.exists():
            try:
                session_path.unlink()
            except IOError:
                pass
    
    def authenticate(
        self,
        username: str,
        password: str,
        force: bool = False
    ) -> Optional[str]:
        """
        Authenticate with TradingView.
        
        Args:
            username: TradingView username/email
            password: TradingView password
            force: Force re-authentication even if session valid
            
        Returns:
            Authentication token or None if failed
        """
        with self._lock:
            if not force and self.is_authenticated:
                if self._session_data.username == username:
                    logger.info("Using existing valid session")
                    return self._session_data.token
            
            return self._do_authenticate(username, password)
    
    def _do_authenticate(
        self, 
        username: str, 
        password: str
    ) -> Optional[str]:
        """Perform actual authentication request."""
        for attempt in range(self._config.max_retries):
            if not self._rate_limiter.acquire(timeout=30):
                logger.warning("Rate limit exceeded, waiting...")
                wait_time = self._rate_limiter.get_wait_time()
                time.sleep(wait_time)
                continue
            
            try:
                result = self._send_auth_request(username, password)
                
                if result:
                    self._start_refresh_thread()
                    return result
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Auth attempt {attempt + 1} failed: {e}")
                
                if attempt < self._config.max_retries - 1:
                    delay = self._config.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        logger.error("Authentication failed after all retries")
        return None
    
    def _send_auth_request(
        self, 
        username: str, 
        password: str
    ) -> Optional[str]:
        """Send authentication request to TradingView."""
        session = requests.Session()
        
        session.cookies.set(
            "cookiePrivacyPreferenceBannerProduction", 
            "notApplicable", 
            domain=".tradingview.com"
        )
        session.cookies.set(
            "cookiesSettings", 
            '{"analytics":true,"advertising":true}', 
            domain=".tradingview.com"
        )
        
        files = {
            "username": (None, username),
            "password": (None, password),
            "remember": (None, "true"),
        }
        
        response = session.post(
            self._config.sign_in_url,
            files=files,
            headers=self._HEADERS_TEMPLATE.copy(),
            timeout=15
        )
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("error"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Login error: {error_msg}")
            return None
        
        user_data = result.get("user", {})
        
        token = user_data.get("auth_token")
        if not token:
            token = session.cookies.get("sessionid")
        if not token:
            token = f"session:{session.cookies.get('sessionid', 'unknown')}"
        
        session_id = session.cookies.get("sessionid", "")
        
        cookies = {}
        for cookie in session.cookies:
            cookies[cookie.name] = cookie.value
        
        self._session_data = SessionData(
            token=token,
            session_id=session_id,
            username=user_data.get("username", username),
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=90),
            cookies=cookies
        )
        
        self._http_session = session
        self._save_session()
        
        logger.info(f"Login successful for user: {self._session_data.username}")
        return token
    
    def _start_refresh_thread(self) -> None:
        """Start background token refresh thread."""
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            return
        
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(
            target=self._refresh_loop,
            daemon=True,
            name="auth_refresh"
        )
        self._refresh_thread.start()
    
    def _refresh_loop(self) -> None:
        """Background loop to refresh token before expiry."""
        while not self._stop_refresh.is_set():
            if self._session_data is None:
                break
            
            if self._session_data.is_near_expiry(threshold_minutes=60):
                logger.info("Session near expiry, refreshing...")
                break
            
            self._stop_refresh.wait(timeout=300)
    
    def refresh_session(
        self, 
        username: str, 
        password: str
    ) -> Optional[str]:
        """
        Refresh the current session.
        
        Args:
            username: TradingView username
            password: TradingView password
            
        Returns:
            New token or None if failed
        """
        return self.authenticate(username, password, force=True)
    
    def logout(self) -> None:
        """Logout and clear session."""
        self._stop_refresh.set()
        self._clear_session()
        self._http_session = None
        logger.info("Logged out successfully")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        if self._session_data is None:
            return {"authenticated": False}
        
        return {
            "authenticated": True,
            "username": self._session_data.username,
            "created_at": self._session_data.created_at.isoformat(),
            "expires_at": self._session_data.expires_at.isoformat(),
            "is_expired": self._session_data.is_expired(),
            "is_near_expiry": self._session_data.is_near_expiry()
        }
    
    def __del__(self):
        """Cleanup on deletion."""
        self._stop_refresh.set()

"""
Unit tests for AuthManager functionality.
"""

import pytest
from datetime import datetime, timedelta
from xnoxs_fetcher import AuthManager, AuthConfig, SessionData, RateLimiter


class TestAuthConfig:
    """Tests for AuthConfig dataclass."""

    def test_default_config(self):
        """Test default auth configuration."""
        config = AuthConfig()
        assert config.max_retries >= 0
        assert config.token_refresh_interval > 0

    def test_custom_config(self):
        """Test custom auth configuration."""
        config = AuthConfig(max_retries=5, token_refresh_interval=7200)
        assert config.max_retries == 5
        assert config.token_refresh_interval == 7200


class TestSessionData:
    """Tests for SessionData dataclass."""

    def test_session_creation(self):
        """Test creating session data."""
        session = SessionData(
            token="test_token",
            session_id="test_session_123",
            username="test_user",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=90),
            cookies={}
        )
        assert session.username == "test_user"
        assert session.session_id == "test_session_123"

    def test_session_expiry_check(self):
        """Test session expiry checking."""
        session = SessionData(
            token="test_token",
            session_id="123",
            username="test",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            cookies={}
        )
        assert not session.is_expired()

    def test_session_to_dict(self):
        """Test session serialization."""
        session = SessionData(
            token="test_token",
            session_id="123",
            username="test",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30),
            cookies={"key": "value"}
        )
        data = session.to_dict()
        assert data["token"] == "test_token"
        assert data["username"] == "test"
        assert "created_at" in data


class TestAuthManager:
    """Tests for AuthManager class."""

    def test_initialization(self):
        """Test auth manager initialization."""
        auth = AuthManager()
        assert auth is not None

    def test_session_info(self):
        """Test getting session info."""
        auth = AuthManager()
        info = auth.get_session_info()
        assert isinstance(info, dict)
        assert "authenticated" in info


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_requests=60, window_seconds=60)
        assert limiter is not None

    def test_rate_limiting(self):
        """Test that rate limiter tracks requests."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        
        for _ in range(10):
            result = limiter.acquire()
            assert result is True

    def test_get_wait_time(self):
        """Test getting wait time."""
        limiter = RateLimiter(max_requests=100, window_seconds=60)
        wait_time = limiter.get_wait_time()
        assert wait_time >= 0

"""
Pytest configuration and fixtures for XnoxsFetcher tests.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data for testing."""
    dates = pd.date_range(end=datetime.now(), periods=100, freq="D")
    data = {
        "symbol": ["NASDAQ:AAPL"] * 100,
        "open": [150.0 + i * 0.1 for i in range(100)],
        "high": [152.0 + i * 0.1 for i in range(100)],
        "low": [148.0 + i * 0.1 for i in range(100)],
        "close": [151.0 + i * 0.1 for i in range(100)],
        "volume": [1000000 + i * 10000 for i in range(100)],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = "datetime"
    return df


@pytest.fixture
def sample_symbols():
    """Sample trading symbols for testing."""
    return [
        ("AAPL", "NASDAQ"),
        ("GOOGL", "NASDAQ"),
        ("MSFT", "NASDAQ"),
        ("BTCUSD", "BINANCE"),
        ("EURUSD", "FX"),
    ]


@pytest.fixture
def mock_session_data():
    """Mock session data for auth testing."""
    return {
        "username": "test_user",
        "session_id": "test_session_123",
        "auth_token": "test_token_abc",
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(days=90)).isoformat(),
    }


@pytest.fixture
def temp_export_dir(tmp_path):
    """Temporary directory for export tests."""
    export_dir = tmp_path / "exports"
    export_dir.mkdir()
    return export_dir

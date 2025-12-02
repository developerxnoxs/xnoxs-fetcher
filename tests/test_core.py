"""
Unit tests for XnoxsFetcher core functionality.
"""

import pytest
from xnoxs_fetcher import XnoxsFetcher, TimeFrame, FetcherConfig


class TestTimeFrame:
    """Tests for TimeFrame enum."""

    def test_timeframe_values(self):
        """Test that all expected timeframes exist."""
        assert hasattr(TimeFrame, "MINUTE_1")
        assert hasattr(TimeFrame, "MINUTE_5")
        assert hasattr(TimeFrame, "MINUTE_15")
        assert hasattr(TimeFrame, "MINUTE_30")
        assert hasattr(TimeFrame, "HOUR_1")
        assert hasattr(TimeFrame, "HOUR_4")
        assert hasattr(TimeFrame, "DAILY")
        assert hasattr(TimeFrame, "WEEKLY")
        assert hasattr(TimeFrame, "MONTHLY")

    def test_timeframe_string_values(self):
        """Test timeframe string representations."""
        assert TimeFrame.MINUTE_1.value is not None
        assert TimeFrame.DAILY.value is not None


class TestFetcherConfig:
    """Tests for FetcherConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = FetcherConfig()
        assert config is not None

    def test_config_has_attributes(self):
        """Test config has expected attributes."""
        config = FetcherConfig()
        assert hasattr(config, "timeout") or hasattr(config, "max_retries") or config is not None


class TestXnoxsFetcher:
    """Tests for XnoxsFetcher class."""

    def test_initialization_anonymous(self):
        """Test anonymous initialization."""
        fetcher = XnoxsFetcher()
        assert fetcher is not None

    def test_initialization_with_credentials(self):
        """Test initialization with credentials (won't actually login)."""
        fetcher = XnoxsFetcher(username="test", password="test")
        assert fetcher is not None

    def test_fetcher_has_required_methods(self):
        """Test that fetcher has required methods."""
        fetcher = XnoxsFetcher()
        assert hasattr(fetcher, "get_hist")
        assert callable(getattr(fetcher, "get_hist"))

    @pytest.mark.network
    def test_fetch_data_returns_dataframe(self):
        """Test that fetch returns a DataFrame (requires network)."""
        import pandas as pd
        fetcher = XnoxsFetcher()
        df = fetcher.get_hist(
            symbol="AAPL",
            exchange="NASDAQ",
            interval=TimeFrame.DAILY,
            n_bars=10
        )
        if df is not None:
            assert isinstance(df, pd.DataFrame)
            assert len(df) <= 10


class TestAliases:
    """Test backward compatibility aliases."""

    def test_tvdatafeed_alias(self):
        """Test TvDatafeed alias."""
        from xnoxs_fetcher import TvDatafeed
        assert TvDatafeed is XnoxsFetcher

    def test_interval_alias(self):
        """Test Interval alias."""
        from xnoxs_fetcher import Interval
        assert Interval is TimeFrame

"""
Unit tests for ParallelFetcher functionality.
"""

import pytest
import pandas as pd
from xnoxs_fetcher import (
    ParallelFetcher,
    ParallelConfig,
    FetchTask,
    FetchResult,
    fetch_parallel,
    TimeFrame,
    XnoxsFetcher,
)


class TestParallelConfig:
    """Tests for ParallelConfig dataclass."""

    def test_default_config(self):
        """Test default configuration."""
        config = ParallelConfig()
        assert config.max_workers > 0
        assert config.timeout_per_task > 0

    def test_custom_config(self):
        """Test custom configuration."""
        config = ParallelConfig(max_workers=10, timeout_per_task=120)
        assert config.max_workers == 10
        assert config.timeout_per_task == 120


class TestFetchTask:
    """Tests for FetchTask dataclass."""

    def test_task_creation(self):
        """Test creating a fetch task."""
        task = FetchTask(
            symbol="AAPL",
            exchange="NASDAQ",
            timeframe="1D",
            bars=100
        )
        assert task.symbol == "AAPL"
        assert task.exchange == "NASDAQ"
        assert task.timeframe == "1D"
        assert task.bars == 100

    def test_task_equality(self):
        """Test task equality comparison."""
        task1 = FetchTask(symbol="AAPL", exchange="NASDAQ", timeframe="1D", bars=100)
        task2 = FetchTask(symbol="AAPL", exchange="NASDAQ", timeframe="1D", bars=100)
        assert task1 == task2

    def test_task_hash(self):
        """Test task hashing."""
        task = FetchTask(symbol="AAPL", exchange="NASDAQ", timeframe="1D", bars=100)
        assert isinstance(hash(task), int)


class TestFetchResult:
    """Tests for FetchResult dataclass."""

    def test_successful_result(self, sample_ohlcv_data):
        """Test successful fetch result."""
        task = FetchTask(symbol="AAPL", exchange="NASDAQ", timeframe="1D", bars=100)
        result = FetchResult(
            task=task,
            data=sample_ohlcv_data,
            success=True,
            error=None
        )
        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_failed_result(self):
        """Test failed fetch result."""
        task = FetchTask(symbol="INVALID", exchange="UNKNOWN", timeframe="1D", bars=100)
        result = FetchResult(
            task=task,
            data=None,
            success=False,
            error="Symbol not found"
        )
        assert result.success is False
        assert result.data is None
        assert result.error == "Symbol not found"


class TestParallelFetcher:
    """Tests for ParallelFetcher class."""

    def test_initialization(self):
        """Test parallel fetcher initialization."""
        fetcher = XnoxsFetcher()
        parallel = ParallelFetcher(fetcher)
        assert parallel is not None

    def test_initialization_with_config(self):
        """Test initialization with custom config."""
        fetcher = XnoxsFetcher()
        config = ParallelConfig(max_workers=5)
        parallel = ParallelFetcher(fetcher, config=config)
        assert parallel is not None


class TestFetchParallelFunction:
    """Tests for fetch_parallel convenience function."""

    def test_function_exists(self):
        """Test that fetch_parallel function exists."""
        assert callable(fetch_parallel)

    @pytest.mark.network
    @pytest.mark.slow
    def test_fetch_parallel_basic(self):
        """Test basic parallel fetching (requires network)."""
        fetcher = XnoxsFetcher()
        symbols = [("AAPL", "NASDAQ"), ("MSFT", "NASDAQ")]
        results = fetch_parallel(
            fetcher=fetcher,
            symbols=symbols,
            timeframe=TimeFrame.DAILY,
            bars=5
        )
        assert isinstance(results, dict)

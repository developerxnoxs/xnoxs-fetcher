"""
XnoxsFetcher Data Models

This module contains data models for symbol sets and data consumers
used in live data streaming.

Author: developerxnoxs
"""

from __future__ import annotations

import queue
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional, Any

import pandas as pd

if TYPE_CHECKING:
    from .live_feed import XnoxsLiveFeed
    from .core import TimeFrame


class SymbolSet:
    """
    Symbol-Exchange-Interval Set (SEIS) Container.
    
    Represents a unique combination of trading symbol, exchange,
    and chart interval. Manages consumers registered for this
    particular data stream.
    
    Attributes:
        symbol: Trading symbol (e.g., "AAPL", "BTCUSD")
        exchange: Exchange name (e.g., "NASDAQ", "BINANCE")
        interval: Chart timeframe interval
        
    Example:
        >>> seis = SymbolSet("AAPL", "NASDAQ", TimeFrame.HOUR_1)
        >>> print(seis)
        symbol='AAPL',exchange='NASDAQ',interval='HOUR_1'
        
    Author: developerxnoxs
    """
    
    __slots__ = (
        "_symbol", "_exchange", "_interval", 
        "_live_feed", "_consumers", "_last_update"
    )
    
    def __init__(
        self, 
        symbol: str, 
        exchange: str, 
        interval: "TimeFrame"
    ) -> None:
        """
        Initialize SymbolSet.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name
            interval: Chart timeframe
        """
        self._symbol = symbol
        self._exchange = exchange
        self._interval = interval
        self._live_feed: Optional["XnoxsLiveFeed"] = None
        self._consumers: List["DataConsumer"] = []
        self._last_update: Optional[Any] = None
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on symbol, exchange, and interval."""
        if not isinstance(other, SymbolSet):
            return NotImplemented
        return (
            self._symbol == other._symbol 
            and self._exchange == other._exchange 
            and self._interval == other._interval
        )
    
    def __repr__(self) -> str:
        """Return machine-readable representation."""
        return f'SymbolSet("{self._symbol}","{self._exchange}",{self._interval})'
    
    def __str__(self) -> str:
        """Return human-readable representation."""
        return (
            f"symbol='{self._symbol}',"
            f"exchange='{self._exchange}',"
            f"interval='{self._interval.name}'"
        )
    
    def __hash__(self) -> int:
        """Make SymbolSet hashable for use in sets/dicts."""
        return hash((self._symbol, self._exchange, self._interval))
    
    @property
    def symbol(self) -> str:
        """Get trading symbol."""
        return self._symbol
    
    @property
    def exchange(self) -> str:
        """Get exchange name."""
        return self._exchange
    
    @property
    def interval(self) -> "TimeFrame":
        """Get chart interval."""
        return self._interval
    
    @property
    def live_feed(self) -> Optional["XnoxsLiveFeed"]:
        """Get associated live feed instance."""
        return self._live_feed
    
    @live_feed.setter
    def live_feed(self, value: "XnoxsLiveFeed") -> None:
        """Set live feed instance."""
        if self._live_feed is not None:
            raise AttributeError(
                "Cannot overwrite live_feed - delete first"
            )
        self._live_feed = value
    
    @live_feed.deleter
    def live_feed(self) -> None:
        """Remove live feed reference."""
        self._live_feed = None
    
    def create_consumer(
        self, 
        callback: Callable[["SymbolSet", pd.DataFrame], None],
        timeout: float = -1
    ) -> "DataConsumer":
        """
        Create and register a new data consumer.
        
        Args:
            callback: Function to call when new data arrives
                     Signature: callback(symbol_set, dataframe)
            timeout: Maximum wait time in seconds (-1 for blocking)
            
        Returns:
            Created DataConsumer instance
            
        Raises:
            RuntimeError: If no live feed is associated
        """
        if self._live_feed is None:
            raise RuntimeError("No live feed associated with this SymbolSet")
        return self._live_feed.create_consumer(self, callback, timeout)
    
    def remove_consumer(
        self, 
        consumer: "DataConsumer",
        timeout: float = -1
    ) -> bool:
        """
        Remove a consumer from this SymbolSet.
        
        Args:
            consumer: Consumer to remove
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False if timed out
        """
        if self._live_feed is None:
            raise RuntimeError("No live feed associated")
        return self._live_feed.remove_consumer(consumer, timeout)
    
    def register_consumer(self, consumer: "DataConsumer") -> None:
        """Internal: Register consumer in list."""
        self._consumers.append(consumer)
    
    def unregister_consumer(self, consumer: "DataConsumer") -> None:
        """Internal: Remove consumer from list."""
        if consumer not in self._consumers:
            raise ValueError("Consumer not found in SymbolSet")
        self._consumers.remove(consumer)
    
    def is_new_data(self, data: pd.DataFrame) -> bool:
        """
        Check if data is newer than last received.
        
        Args:
            data: DataFrame with datetime index
            
        Returns:
            True if data is new, False otherwise
        """
        current_time = data.index.to_pydatetime()[0]
        if self._last_update != current_time:
            self._last_update = current_time
            return True
        return False
    
    def get_historical_data(
        self, 
        bars: int = 10,
        timeout: float = -1
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data for this SymbolSet.
        
        Args:
            bars: Number of bars to retrieve
            timeout: Maximum wait time in seconds
            
        Returns:
            DataFrame with OHLCV data
            
        Raises:
            RuntimeError: If no live feed is associated
        """
        if self._live_feed is None:
            raise RuntimeError("No live feed associated")
        return self._live_feed.get_historical_data(
            symbol=self._symbol,
            exchange=self._exchange,
            timeframe=self._interval,
            bars=bars,
            timeout=timeout
        )
    
    def remove(self, timeout: float = -1) -> bool:
        """
        Remove this SymbolSet from live feed.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False if timed out
        """
        if self._live_feed is None:
            raise RuntimeError("No live feed associated")
        return self._live_feed.remove_symbol_set(self, timeout)
    
    def get_consumers(self) -> List["DataConsumer"]:
        """Get list of registered consumers."""
        return self._consumers.copy()


class DataConsumer(threading.Thread):
    """
    Asynchronous Data Consumer.
    
    Runs in a separate thread, processing incoming market data
    and invoking callback functions for each new data bar.
    
    Attributes:
        symbol_set: Associated SymbolSet
        callback: Function to invoke on new data
        
    Example:
        >>> def on_data(seis, data):
        ...     print(f"New data: {data['close'].iloc[0]}")
        >>> consumer = live_feed.create_consumer(seis, on_data)
        
    Author: developerxnoxs
    """
    
    __slots__ = ("_buffer", "symbol_set", "callback")
    
    def __init__(
        self, 
        symbol_set: SymbolSet,
        callback: Callable[[SymbolSet, pd.DataFrame], None]
    ) -> None:
        """
        Initialize DataConsumer.
        
        Args:
            symbol_set: SymbolSet to consume data from
            callback: Function to call with new data
        """
        super().__init__()
        self._buffer: queue.Queue[Optional[pd.DataFrame]] = queue.Queue()
        self.symbol_set = symbol_set
        self.callback = callback
        
        self.name = (
            f"{callback.__name__}_"
            f"{symbol_set.symbol}_"
            f"{symbol_set.exchange}_"
            f"{symbol_set.interval.value}"
        )
    
    def __repr__(self) -> str:
        """Return machine-readable representation."""
        return f"DataConsumer({repr(self.symbol_set)},{self.callback.__name__})"
    
    def __str__(self) -> str:
        """Return human-readable representation."""
        return f"{repr(self.symbol_set)},callback={self.callback.__name__}"
    
    def run(self) -> None:
        """Thread main loop - process data queue."""
        while True:
            data = self._buffer.get()
            
            if data is None:
                break
            
            try:
                self.callback(self.symbol_set, data)
            except Exception as exc:
                self.remove()
                self.symbol_set = None  # type: ignore
                self.callback = None  # type: ignore
                self._buffer = None  # type: ignore
                raise exc from None
        
        self.symbol_set = None  # type: ignore
        self.callback = None  # type: ignore
        self._buffer = None  # type: ignore
    
    def enqueue(self, data: Optional[pd.DataFrame]) -> None:
        """
        Add data to processing queue.
        
        Args:
            data: DataFrame to process, or None to stop
        """
        self._buffer.put(data)
    
    def remove(self, timeout: float = -1) -> bool:
        """
        Stop consumer and remove from SymbolSet.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False if timed out
        """
        return self.symbol_set.remove_consumer(self, timeout)
    
    def stop(self) -> None:
        """Signal thread to stop processing."""
        self._buffer.put(None)


# Backward compatibility aliases
Seis = SymbolSet
Consumer = DataConsumer

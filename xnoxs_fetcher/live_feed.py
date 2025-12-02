"""
XnoxsFetcher Live Feed Module

This module provides real-time data streaming capabilities
with callback-based consumer pattern.

Author: developerxnoxs
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional, Any, Tuple

import pandas as pd
from dateutil.relativedelta import relativedelta

from .core import XnoxsFetcher, TimeFrame
from .models import SymbolSet, DataConsumer

logger = logging.getLogger(__name__)

RETRY_LIMIT = 50


class IntervalTracker(dict):
    """
    Internal class for managing interval groups and trigger times.
    
    Tracks multiple SymbolSets organized by their intervals,
    and manages waiting for the next data update.
    """
    
    _TIMEFRAME_DELTAS = {
        "1": relativedelta(minutes=1),
        "3": relativedelta(minutes=3),
        "5": relativedelta(minutes=5),
        "15": relativedelta(minutes=15),
        "30": relativedelta(minutes=30),
        "45": relativedelta(minutes=45),
        "1H": relativedelta(hours=1),
        "2H": relativedelta(hours=2),
        "3H": relativedelta(hours=3),
        "4H": relativedelta(hours=4),
        "1D": relativedelta(days=1),
        "1W": relativedelta(weeks=1),
        "1M": relativedelta(months=1),
    }
    
    def __init__(self) -> None:
        super().__init__()
        self._shutdown_flag = False
        self._next_trigger: Optional[datetime] = None
        self._interrupt_event = threading.Event()
    
    def _calculate_next_trigger(self) -> Optional[datetime]:
        """Get the soonest expiry datetime across all intervals."""
        if not self.values():
            return None
        
        trigger_times = [values[1] for values in self.values()]
        trigger_times.sort()
        return trigger_times[0]
    
    def find_symbol_set(
        self, 
        symbol: str, 
        exchange: str, 
        interval: TimeFrame
    ) -> Optional[SymbolSet]:
        """Find existing SymbolSet by parameters."""
        for seis in self:
            if (
                seis.symbol == symbol 
                and seis.exchange == exchange 
                and seis.interval == interval
            ):
                return seis
        return None
    
    def wait_for_trigger(self) -> bool:
        """
        Wait until next interval expires.
        
        Returns:
            True if wait completed normally
            False if shutdown requested
        """
        if not self._shutdown_flag:
            self._interrupt_event.clear()
        
        self._next_trigger = self._calculate_next_trigger()
        
        while True:
            wait_duration = (self._next_trigger - datetime.now()).total_seconds()
            
            interrupted = self._interrupt_event.wait(wait_duration)
            
            if interrupted and self._shutdown_flag:
                return False
            
            if not interrupted:
                self._interrupt_event.clear()
                break
        
        return True
    
    def get_expired_intervals(self) -> List[str]:
        """Get intervals that have expired and update their next trigger times."""
        expired = []
        now = datetime.now()
        
        for interval_key, values in self.items():
            if now >= values[1]:
                expired.append(interval_key)
                values[1] = values[1] + self._TIMEFRAME_DELTAS[interval_key]
        
        return expired
    
    def request_shutdown(self) -> None:
        """Signal shutdown and interrupt waiting."""
        self._shutdown_flag = True
        self._interrupt_event.set()
    
    def add_symbol_set(
        self, 
        seis: SymbolSet,
        update_time: Optional[datetime] = None
    ) -> None:
        """Add SymbolSet to tracking."""
        if self:
            self._shutdown_flag = False
            self._interrupt_event.clear()
        
        interval_key = seis.interval.value
        
        if interval_key in self.keys():
            super().__getitem__(interval_key)[0].append(seis)
        else:
            if update_time is None:
                raise ValueError("update_time required for new interval group")
            
            next_trigger = update_time + self._TIMEFRAME_DELTAS[interval_key]
            self[interval_key] = [[seis], next_trigger]
            
            calculated_trigger = self._calculate_next_trigger()
            if calculated_trigger != self._next_trigger:
                self._next_trigger = calculated_trigger
                self._interrupt_event.set()
    
    def remove_symbol_set(self, seis: SymbolSet) -> None:
        """Remove SymbolSet from tracking."""
        if seis not in self:
            raise KeyError("SymbolSet not found in tracker")
        
        interval_key = seis.interval.value
        super().__getitem__(interval_key)[0].remove(seis)
        
        if not super().__getitem__(interval_key)[0]:
            self.pop(interval_key)
            
            calculated_trigger = self._calculate_next_trigger()
            if calculated_trigger != self._next_trigger and not self._shutdown_flag:
                self._next_trigger = calculated_trigger
                self._interrupt_event.set()
    
    def get_intervals(self) -> List[str]:
        """Get list of tracked interval keys."""
        return list(self.keys())
    
    def __getitem__(self, interval_key: str) -> List[SymbolSet]:
        """Get SymbolSets for an interval."""
        return super().__getitem__(interval_key)[0]
    
    def __iter__(self):
        """Iterate over all SymbolSets."""
        all_sets = []
        for seis_list in super().values():
            all_sets.extend(seis_list[0])
        return iter(all_sets)
    
    def __contains__(self, seis: object) -> bool:
        """Check if SymbolSet is tracked."""
        for seis_list in super().values():
            if seis in seis_list[0]:
                return True
        return False


class XnoxsLiveFeed(XnoxsFetcher):
    """
    Real-time TradingView Data Feed.
    
    Extends XnoxsFetcher with live data streaming capabilities.
    Supports multiple symbol-exchange-interval sets with 
    callback-based data consumption.
    
    Features:
        - Automatic interval-based data fetching
        - Multiple consumers per symbol set
        - Thread-safe operations
        - Graceful shutdown handling
        
    Example:
        >>> live = XnoxsLiveFeed()
        >>> seis = live.create_symbol_set("BTCUSD", "BINANCE", TimeFrame.MINUTE_1)
        >>> 
        >>> def on_price(seis, data):
        ...     print(f"BTC: ${data['close'].iloc[0]:.2f}")
        >>> 
        >>> consumer = seis.create_consumer(on_price)
        
    Author: developerxnoxs
    """
    
    __slots__ = ("_lock", "_main_thread", "_tracker")
    
    def __init__(
        self, 
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        """
        Initialize XnoxsLiveFeed.
        
        Args:
            username: TradingView username (optional)
            password: TradingView password (optional)
        """
        super().__init__(username, password)
        self._lock = threading.Lock()
        self._main_thread: Optional[threading.Thread] = None
        self._tracker = IntervalTracker()
    
    def _validate_symbol(self, symbol: str, exchange: str) -> bool:
        """Check if symbol exists on TradingView."""
        results = self.search_symbols(symbol, exchange)
        
        if not results:
            return False
        
        for item in results:
            if item.get("symbol") == symbol and item.get("exchange") == exchange:
                return True
        
        return False
    
    def create_symbol_set(
        self,
        symbol: str,
        exchange: str,
        interval: TimeFrame,
        timeout: float = -1
    ) -> SymbolSet:
        """
        Create and register a new SymbolSet for live tracking.
        
        Args:
            symbol: Trading symbol
            exchange: Exchange name  
            interval: Chart timeframe
            timeout: Maximum wait time in seconds (-1 for blocking)
            
        Returns:
            Created or existing SymbolSet
            
        Raises:
            ValueError: If symbol/exchange combination not found
        """
        existing = self._tracker.find_symbol_set(symbol, exchange, interval)
        if existing:
            return existing
        
        new_seis = SymbolSet(symbol, exchange, interval)
        
        acquired = self._lock.acquire(timeout=timeout if timeout > 0 else -1)
        if not acquired:
            raise TimeoutError("Lock acquisition timed out")
        
        try:
            new_seis.live_feed = self
            
            if new_seis in self._tracker:
                return self._tracker.find_symbol_set(symbol, exchange, interval)
            
            interval_key = new_seis.interval.value
            
            if interval_key not in self._tracker.get_intervals():
                ticker_data = super().get_historical_data(
                    new_seis.symbol,
                    new_seis.exchange,
                    new_seis.interval,
                    bars=2
                )
                update_time = ticker_data.index.to_pydatetime()[0]
                self._tracker.add_symbol_set(new_seis, update_time)
            else:
                self._tracker.add_symbol_set(new_seis)
        finally:
            self._lock.release()
        
        if self._main_thread is None:
            self._main_thread = threading.Thread(
                name="xnoxs_live_feed",
                target=self._data_loop,
                daemon=True
            )
            self._main_thread.start()
        
        return new_seis
    
    def remove_symbol_set(
        self, 
        seis: SymbolSet,
        timeout: float = -1
    ) -> bool:
        """
        Remove SymbolSet from live tracking.
        
        Args:
            seis: SymbolSet to remove
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False if timed out
        """
        if seis not in self._tracker:
            raise ValueError("SymbolSet not registered")
        
        acquired = self._lock.acquire(timeout=timeout if timeout > 0 else -1)
        if not acquired:
            return False
        
        try:
            for consumer in seis.get_consumers():
                consumer.enqueue(None)
            
            self._tracker.remove_symbol_set(seis)
            del seis.live_feed
            
            if not self._tracker:
                self._tracker.request_shutdown()
        finally:
            self._lock.release()
        
        return True
    
    def create_consumer(
        self,
        seis: SymbolSet,
        callback: Callable[[SymbolSet, pd.DataFrame], None],
        timeout: float = -1
    ) -> DataConsumer:
        """
        Create a new data consumer for SymbolSet.
        
        Args:
            seis: SymbolSet to consume data from
            callback: Function to call on new data
            timeout: Maximum wait time in seconds
            
        Returns:
            Created DataConsumer instance
        """
        if seis not in self._tracker:
            raise ValueError("SymbolSet not registered")
        
        consumer = DataConsumer(seis, callback)
        
        acquired = self._lock.acquire(timeout=timeout if timeout > 0 else -1)
        if not acquired:
            raise TimeoutError("Lock acquisition timed out")
        
        try:
            seis.register_consumer(consumer)
            consumer.start()
        finally:
            self._lock.release()
        
        return consumer
    
    def remove_consumer(
        self, 
        consumer: DataConsumer,
        timeout: float = -1
    ) -> bool:
        """
        Remove consumer from its SymbolSet.
        
        Args:
            consumer: Consumer to remove
            timeout: Maximum wait time in seconds
            
        Returns:
            True if successful, False if timed out
        """
        acquired = self._lock.acquire(timeout=timeout if timeout > 0 else -1)
        if not acquired:
            return False
        
        try:
            consumer.symbol_set.unregister_consumer(consumer)
            consumer.stop()
        finally:
            self._lock.release()
        
        return True
    
    def _data_loop(self) -> None:
        """Main data fetching loop (runs in background thread)."""
        while self._tracker.wait_for_trigger():
            with self._lock:
                for interval_key in self._tracker.get_expired_intervals():
                    for seis in self._tracker[interval_key]:
                        data: Optional[pd.DataFrame] = None
                        
                        for attempt in range(RETRY_LIMIT):
                            data = super().get_historical_data(
                                seis.symbol,
                                seis.exchange,
                                timeframe=seis.interval,
                                bars=2
                            )
                            
                            if data is not None and seis.is_new_data(data):
                                data = data.drop(labels=data.index[1])
                                break
                            
                            time.sleep(0.1)
                        else:
                            self._tracker.request_shutdown()
                            logger.critical(
                                "Failed to fetch data from TradingView"
                            )
                            continue
                        
                        for consumer in seis.get_consumers():
                            consumer.enqueue(data)
        
        with self._lock:
            for seis in list(self._tracker):
                for consumer in seis.get_consumers():
                    seis.unregister_consumer(consumer)
                    consumer.stop()
                
                self._tracker.remove_symbol_set(seis)
            
            self._main_thread = None
    
    def get_historical_data(
        self,
        symbol: str,
        exchange: str = "NSE",
        timeframe: TimeFrame = TimeFrame.DAILY,
        bars: int = 10,
        futures_contract: Optional[int] = None,
        extended_session: bool = False,
        timeout: float = -1,
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data (thread-safe version).
        
        Overrides parent method to add thread safety.
        See XnoxsFetcher.get_historical_data for full documentation.
        """
        acquired = self._lock.acquire(timeout=timeout if timeout > 0 else -1)
        if not acquired:
            return None
        
        try:
            return super().get_historical_data(
                symbol, exchange, timeframe,
                bars, futures_contract, extended_session
            )
        finally:
            self._lock.release()
    
    def shutdown(self) -> None:
        """Stop all consumers and close live feed."""
        if self._main_thread is not None:
            with self._lock:
                self._tracker.request_shutdown()
            self._main_thread.join()
    
    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.shutdown()


# Backward compatibility alias
TvDatafeedLive = XnoxsLiveFeed

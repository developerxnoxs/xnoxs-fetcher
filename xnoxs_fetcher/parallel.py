"""
XnoxsFetcher Parallel Module

This module provides parallel/async data fetching capabilities
for retrieving data from multiple symbols simultaneously.

Author: developerxnoxs
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Callable, Union, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FetchTask:
    """Represents a single fetch task."""
    symbol: str
    exchange: str
    timeframe: str
    bars: int = 100
    futures_contract: Optional[int] = None
    extended_session: bool = False
    
    def __hash__(self):
        return hash((self.symbol, self.exchange, self.timeframe, self.bars))
    
    def __eq__(self, other):
        if not isinstance(other, FetchTask):
            return False
        return (
            self.symbol == other.symbol and
            self.exchange == other.exchange and
            self.timeframe == other.timeframe and
            self.bars == other.bars
        )


@dataclass
class FetchResult:
    """Result of a fetch operation."""
    task: FetchTask
    data: Optional[pd.DataFrame]
    success: bool
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class ParallelConfig:
    """Configuration for parallel fetcher."""
    max_workers: int = 5
    timeout_per_task: float = 60.0
    retry_count: int = 2
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.5


class ParallelFetcher:
    """
    Parallel Data Fetcher for multiple symbols.
    
    Features:
        - Concurrent data fetching with thread pool
        - Progress tracking and callbacks
        - Error handling and retry logic
        - Rate limiting to avoid API blocks
    
    Example:
        >>> from xnoxs_fetcher import XnoxsFetcher, TimeFrame
        >>> fetcher = XnoxsFetcher()
        >>> parallel = ParallelFetcher(fetcher)
        >>> 
        >>> symbols = [
        ...     ("AAPL", "NASDAQ"),
        ...     ("GOOGL", "NASDAQ"),
        ...     ("MSFT", "NASDAQ")
        ... ]
        >>> results = parallel.fetch_multiple(symbols, TimeFrame.DAILY, bars=100)
    
    Author: developerxnoxs
    """
    
    def __init__(
        self,
        fetcher: Any,
        config: Optional[ParallelConfig] = None,
        on_progress: Optional[Callable[[int, int, FetchResult], None]] = None,
        on_complete: Optional[Callable[[List[FetchResult]], None]] = None
    ):
        """
        Initialize ParallelFetcher.
        
        Args:
            fetcher: XnoxsFetcher instance
            config: Parallel configuration
            on_progress: Callback for progress updates (completed, total, result)
            on_complete: Callback when all tasks complete
        """
        self._fetcher = fetcher
        self._config = config or ParallelConfig()
        self._on_progress = on_progress
        self._on_complete = on_complete
        self._lock = threading.Lock()
        self._completed_count = 0
        self._results: List[FetchResult] = []
    
    def _fetch_single(self, task: FetchTask) -> FetchResult:
        """
        Fetch data for a single task.
        
        Args:
            task: Fetch task to execute
            
        Returns:
            FetchResult with data or error
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self._config.retry_count + 1):
            try:
                time.sleep(self._config.rate_limit_delay)
                
                from .core import TimeFrame
                timeframe = TimeFrame.from_string(task.timeframe)
                
                data = self._fetcher.get_historical_data(
                    symbol=task.symbol,
                    exchange=task.exchange,
                    timeframe=timeframe,
                    bars=task.bars,
                    futures_contract=task.futures_contract,
                    extended_session=task.extended_session
                )
                
                duration = time.time() - start_time
                
                if data is not None and not data.empty:
                    return FetchResult(
                        task=task,
                        data=data,
                        success=True,
                        duration_seconds=duration
                    )
                else:
                    last_error = "No data returned"
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Fetch attempt {attempt + 1} failed for "
                    f"{task.symbol}:{task.exchange}: {e}"
                )
                
                if attempt < self._config.retry_count:
                    time.sleep(self._config.retry_delay * (attempt + 1))
        
        duration = time.time() - start_time
        return FetchResult(
            task=task,
            data=None,
            success=False,
            error=last_error,
            duration_seconds=duration
        )
    
    def fetch_multiple(
        self,
        symbols: List[Tuple[str, str]],
        timeframe: Any,
        bars: int = 100,
        futures_contract: Optional[int] = None,
        extended_session: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols in parallel.
        
        Args:
            symbols: List of (symbol, exchange) tuples
            timeframe: Chart timeframe
            bars: Number of bars per symbol
            futures_contract: Futures contract number
            extended_session: Include extended hours
            
        Returns:
            Dictionary mapping "SYMBOL:EXCHANGE" to DataFrame
        """
        timeframe_str = timeframe.value if hasattr(timeframe, 'value') else str(timeframe)
        
        tasks = [
            FetchTask(
                symbol=sym,
                exchange=exch,
                timeframe=timeframe_str,
                bars=bars,
                futures_contract=futures_contract,
                extended_session=extended_session
            )
            for sym, exch in symbols
        ]
        
        results = self.fetch_tasks(tasks)
        
        output = {}
        for result in results:
            if result.success and result.data is not None:
                key = f"{result.task.symbol}:{result.task.exchange}"
                output[key] = result.data
        
        return output
    
    def fetch_tasks(self, tasks: List[FetchTask]) -> List[FetchResult]:
        """
        Execute multiple fetch tasks in parallel.
        
        Args:
            tasks: List of FetchTask objects
            
        Returns:
            List of FetchResult objects
        """
        self._completed_count = 0
        self._results = []
        total_tasks = len(tasks)
        
        logger.info(f"Starting parallel fetch of {total_tasks} symbols")
        
        with ThreadPoolExecutor(max_workers=self._config.max_workers) as executor:
            futures: Dict[Future, FetchTask] = {
                executor.submit(self._fetch_single, task): task
                for task in tasks
            }
            
            for future in as_completed(futures, timeout=self._config.timeout_per_task * total_tasks):
                task = futures[future]
                
                try:
                    result = future.result(timeout=self._config.timeout_per_task)
                except Exception as e:
                    result = FetchResult(
                        task=task,
                        data=None,
                        success=False,
                        error=str(e)
                    )
                
                with self._lock:
                    self._completed_count += 1
                    self._results.append(result)
                    
                    if self._on_progress:
                        try:
                            self._on_progress(
                                self._completed_count, 
                                total_tasks, 
                                result
                            )
                        except Exception as e:
                            logger.error(f"Progress callback error: {e}")
                
                status = "OK" if result.success else f"FAILED: {result.error}"
                logger.info(
                    f"[{self._completed_count}/{total_tasks}] "
                    f"{task.symbol}:{task.exchange} - {status}"
                )
        
        if self._on_complete:
            try:
                self._on_complete(self._results)
            except Exception as e:
                logger.error(f"Complete callback error: {e}")
        
        successful = sum(1 for r in self._results if r.success)
        logger.info(
            f"Parallel fetch complete: {successful}/{total_tasks} successful"
        )
        
        return self._results
    
class BatchExporter:
    """
    Batch export for parallel fetch results.
    """
    
    @staticmethod
    def results_to_combined_df(
        results: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Combine multiple DataFrames into one.
        
        Args:
            results: Dictionary of symbol -> DataFrame
            
        Returns:
            Combined DataFrame with all data
        """
        if not results:
            return pd.DataFrame()
        
        dfs = []
        for key, df in results.items():
            df_copy = df.copy()
            if 'symbol' not in df_copy.columns:
                df_copy.insert(0, 'symbol', key)
            dfs.append(df_copy)
        
        return pd.concat(dfs, ignore_index=False)
    
    @staticmethod
    def results_summary(results: List[FetchResult]) -> Dict[str, Any]:
        """
        Generate summary statistics for fetch results.
        
        Args:
            results: List of FetchResult objects
            
        Returns:
            Summary dictionary
        """
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        total_rows = sum(
            len(r.data) for r in successful if r.data is not None
        )
        
        avg_duration = (
            sum(r.duration_seconds for r in results) / len(results)
            if results else 0
        )
        
        return {
            "total_tasks": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100 if results else 0,
            "total_rows_fetched": total_rows,
            "average_duration_seconds": round(avg_duration, 2),
            "failed_symbols": [
                f"{r.task.symbol}:{r.task.exchange}" 
                for r in failed
            ],
            "errors": {
                f"{r.task.symbol}:{r.task.exchange}": r.error 
                for r in failed if r.error
            }
        }


def fetch_parallel(
    fetcher: Any,
    symbols: List[Tuple[str, str]],
    timeframe: Any,
    bars: int = 100,
    max_workers: int = 5,
    show_progress: bool = True,
    progress_callback: Optional[Callable[[str, str, bool, int, int], None]] = None
) -> Dict[Tuple[str, str], pd.DataFrame]:
    """
    Quick parallel fetch function.
    
    Args:
        fetcher: XnoxsFetcher instance
        symbols: List of (symbol, exchange) tuples
        timeframe: Chart timeframe
        bars: Number of bars
        max_workers: Number of parallel workers
        show_progress: Print progress to console
        progress_callback: Optional callback(symbol, exchange, success, current, total)
        
    Returns:
        Dictionary mapping (symbol, exchange) tuple to DataFrame
    
    Example:
        >>> results = fetch_parallel(
        ...     fetcher,
        ...     [("AAPL", "NASDAQ"), ("GOOGL", "NASDAQ")],
        ...     TimeFrame.DAILY,
        ...     bars=100
        ... )
    """
    output: Dict[Tuple[str, str], pd.DataFrame] = {}
    to_fetch: List[Tuple[str, str]] = list(symbols)
    
    if to_fetch:
        def internal_progress(completed, total, result):
            if show_progress:
                status = "OK" if result.success else "FAILED"
                print(f"  [{completed}/{total}] {result.task.symbol} - {status}")
            if progress_callback:
                try:
                    progress_callback(
                        result.task.symbol,
                        result.task.exchange,
                        result.success,
                        completed,
                        total
                    )
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
        
        config = ParallelConfig(max_workers=max_workers)
        parallel = ParallelFetcher(
            fetcher, 
            config=config,
            on_progress=internal_progress if (show_progress or progress_callback) else None
        )
        
        results = parallel.fetch_multiple(to_fetch, timeframe, bars)
        
        for key, df in results.items():
            parts = key.split(":")
            if len(parts) >= 2:
                sym, exch = parts[0], parts[1]
                output[(sym, exch)] = df
    
    return output

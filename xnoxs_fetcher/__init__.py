"""
XnoxsFetcher - Advanced TradingView Data Fetcher

A powerful Python library for fetching historical and live market data 
from TradingView. Supports multiple exchanges, timeframes, and real-time
data streaming with callback-based consumers.

Author: developerxnoxs
License: MIT License
Version: 3.0.0
"""

from __future__ import annotations

from .core import XnoxsFetcher, TimeFrame, FetcherConfig
from .live_feed import XnoxsLiveFeed
from .models import SymbolSet, DataConsumer

__version__ = "3.0.0"
__author__ = "developerxnoxs"

TvDatafeed = XnoxsFetcher
Interval = TimeFrame
TvDatafeedLive = XnoxsLiveFeed
Seis = SymbolSet
Consumer = DataConsumer

__all__ = [
    "XnoxsFetcher",
    "XnoxsLiveFeed", 
    "TimeFrame",
    "SymbolSet",
    "DataConsumer",
    "FetcherConfig",
    "TvDatafeed",
    "Interval",
    "TvDatafeedLive",
    "Seis",
    "Consumer",
]

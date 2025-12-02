#!/usr/bin/env python3
"""
XnoxsFetcher Demo Script

Demonstrates the capabilities of the xnoxs_fetcher library
for fetching market data from TradingView.

Author: developerxnoxs
"""

from __future__ import annotations

import sys
from typing import Optional

import pandas as pd

from xnoxs_fetcher import XnoxsFetcher, TimeFrame


def print_header(title: str, char: str = "=") -> None:
    """Print formatted section header."""
    line = char * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}\n")


def print_subheader(title: str) -> None:
    """Print formatted subsection header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}\n")


def display_dataframe(df: Optional[pd.DataFrame], name: str) -> bool:
    """Display dataframe with formatting."""
    if df is None or df.empty:
        print(f"  [ERROR] Failed to retrieve {name} data")
        return False
    
    print(df.to_string())
    print(f"\n  [OK] Retrieved {len(df)} bars of {name} data")
    return True


def demo_basic_fetch(fetcher: XnoxsFetcher) -> None:
    """Demonstrate basic data fetching."""
    print_subheader("Basic Data Fetching - Apple (AAPL)")
    
    data = fetcher.get_historical_data(
        symbol="AAPL",
        exchange="NASDAQ",
        timeframe=TimeFrame.DAILY,
        bars=10
    )
    display_dataframe(data, "AAPL")


def demo_crypto_fetch(fetcher: XnoxsFetcher) -> None:
    """Demonstrate cryptocurrency data fetching."""
    print_subheader("Cryptocurrency - Bitcoin (BTCUSD)")
    
    data = fetcher.get_historical_data(
        symbol="BTCUSD",
        exchange="BINANCE",
        timeframe=TimeFrame.HOUR_1,
        bars=10
    )
    display_dataframe(data, "BTCUSD")


def demo_different_timeframes(fetcher: XnoxsFetcher) -> None:
    """Demonstrate different timeframe options."""
    print_subheader("Multiple Timeframes - Ethereum")
    
    timeframes = [
        (TimeFrame.MINUTE_15, "15-minute"),
        (TimeFrame.HOUR_4, "4-hour"),
        (TimeFrame.DAILY, "Daily"),
    ]
    
    for tf, name in timeframes:
        print(f"\n  {name} timeframe:")
        data = fetcher.get_historical_data(
            symbol="ETHUSDT",
            exchange="BINANCE",
            timeframe=tf,
            bars=5
        )
        if data is not None:
            print(f"    Latest close: ${data['close'].iloc[-1]:,.2f}")
            print(f"    Volume: {data['volume'].iloc[-1]:,.0f}")


def demo_symbol_search(fetcher: XnoxsFetcher) -> None:
    """Demonstrate symbol search functionality."""
    print_subheader("Symbol Search")
    
    queries = [
        ("TSLA", "NASDAQ"),
        ("BTC", ""),
    ]
    
    for query, exchange in queries:
        filter_text = f" on {exchange}" if exchange else ""
        print(f"  Searching for '{query}'{filter_text}...")
        
        results = fetcher.search_symbols(query, exchange)
        
        if results:
            print(f"  Found {len(results)} result(s):")
            for i, r in enumerate(results[:3], 1):
                symbol = r.get("symbol", "N/A")
                desc = r.get("description", "N/A")
                exch = r.get("exchange", "N/A")
                print(f"    {i}. {exch}:{symbol} - {desc}")
        else:
            print("  No results found")
        print()


def demo_available_timeframes() -> None:
    """Display all available timeframes."""
    print_subheader("Available Timeframes")
    
    print("  XnoxsFetcher supports the following timeframes:\n")
    
    categories = {
        "Minutes": [TimeFrame.MINUTE_1, TimeFrame.MINUTE_3, TimeFrame.MINUTE_5,
                   TimeFrame.MINUTE_15, TimeFrame.MINUTE_30, TimeFrame.MINUTE_45],
        "Hours": [TimeFrame.HOUR_1, TimeFrame.HOUR_2, TimeFrame.HOUR_3, TimeFrame.HOUR_4],
        "Days+": [TimeFrame.DAILY, TimeFrame.WEEKLY, TimeFrame.MONTHLY],
    }
    
    for category, timeframes in categories.items():
        tf_names = [tf.name for tf in timeframes]
        print(f"  {category}: {', '.join(tf_names)}")


def main() -> int:
    """Run the demo."""
    print_header("XnoxsFetcher Demo", "═")
    print("  Advanced TradingView Data Fetcher")
    print("  Author: developerxnoxs")
    print("  Version: 3.0.0")
    
    print("\n  Initializing XnoxsFetcher...")
    print("  NOTE: Running in anonymous mode (limited data access)")
    
    try:
        fetcher = XnoxsFetcher()
        print("  [OK] Fetcher initialized successfully")
    except Exception as exc:
        print(f"  [ERROR] Failed to initialize: {exc}")
        return 1
    
    demo_basic_fetch(fetcher)
    demo_crypto_fetch(fetcher)
    demo_different_timeframes(fetcher)
    demo_symbol_search(fetcher)
    demo_available_timeframes()
    
    print_header("Demo Complete", "═")
    print("  For authenticated access, initialize with credentials:")
    print("    fetcher = XnoxsFetcher(username='...', password='...')")
    print()
    print("  For live data streaming, use XnoxsLiveFeed:")
    print("    from xnoxs_fetcher import XnoxsLiveFeed, TimeFrame")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

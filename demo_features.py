#!/usr/bin/env python3
"""
XnoxsFetcher New Features Demo

Demonstrates the new features:
1. Auth Manager - Session management
2. Export - CSV/Excel/JSON export
3. Parallel - Multi-symbol fetching

Author: developerxnoxs
"""

import os
import sys
import time

from xnoxs_fetcher import (
    XnoxsFetcher,
    TimeFrame,
    AuthManager,
    DataExporter,
    ParallelFetcher,
    fetch_parallel,
)


def print_header(title: str) -> None:
    """Print formatted section header."""
    line = "=" * 60
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}\n")


def demo_auth_manager():
    """Demo: Auth Manager with session persistence."""
    print_header("1. AUTH MANAGER DEMO")
    
    username = os.environ.get("TRADINGVIEW_USERNAME")
    password = os.environ.get("TRADINGVIEW_PASSWORD")
    
    if not username or not password:
        print("  [SKIP] No credentials found in environment")
        print("  Set TRADINGVIEW_USERNAME and TRADINGVIEW_PASSWORD to test")
        return None
    
    print("  Initializing Auth Manager...")
    auth = AuthManager()
    
    print(f"  Session info: {auth.get_session_info()}")
    
    print("  Authenticating...")
    token = auth.authenticate(username, password)
    
    if token:
        print(f"  [OK] Login successful!")
        print(f"  Username: {auth.username}")
        print(f"  Token: {token[:30]}...")
        print(f"  Session info: {auth.get_session_info()}")
    else:
        print("  [FAILED] Login failed")
    
    return auth


def demo_export(data=None):
    """Demo: Data export."""
    print_header("2. EXPORT DEMO")
    
    if data is None:
        print("  Fetching sample data...")
        fetcher = XnoxsFetcher()
        data = fetcher.get_historical_data("AAPL", "NASDAQ", TimeFrame.DAILY, 20)
    
    if data is None:
        print("  [SKIP] No data available for export")
        return
    
    print(f"  Data to export: {len(data)} rows")
    
    exporter = DataExporter(output_dir="exports")
    
    print("\n  Exporting to CSV...")
    csv_path = exporter.to_csv(data, "AAPL_daily")
    print(f"  [OK] Exported: {csv_path}")
    
    print("\n  Exporting to JSON...")
    json_path = exporter.to_json(data, "AAPL_daily")
    print(f"  [OK] Exported: {json_path}")
    
    print("\n  Exporting to Excel...")
    try:
        excel_path = exporter.to_excel(data, "AAPL_daily", sheet_name="Daily Data")
        print(f"  [OK] Exported: {excel_path}")
    except Exception as e:
        print(f"  [WARN] Excel export issue: {e}")
    
    print("\n  Creating summary report...")
    report_path = exporter.create_summary_report(data, "AAPL_report")
    print(f"  [OK] Report: {report_path}")
    
    with open(report_path, 'r') as f:
        print("\n  Report preview:")
        for line in f.readlines()[:15]:
            print(f"    {line.rstrip()}")


def demo_parallel():
    """Demo: Parallel fetching."""
    print_header("3. PARALLEL FETCH DEMO")
    
    fetcher = XnoxsFetcher()
    
    symbols = [
        ("AAPL", "NASDAQ"),
        ("GOOGL", "NASDAQ"),
        ("MSFT", "NASDAQ"),
        ("AMZN", "NASDAQ"),
        ("META", "NASDAQ"),
    ]
    
    print(f"  Fetching {len(symbols)} symbols in parallel...")
    print("  Symbols:", [s[0] for s in symbols])
    print()
    
    start = time.time()
    results = fetch_parallel(
        fetcher,
        symbols,
        TimeFrame.DAILY,
        bars=10,
        max_workers=3,
        show_progress=True
    )
    duration = time.time() - start
    
    print(f"\n  Total time: {duration:.2f}s")
    print(f"  Average per symbol: {duration / len(symbols):.2f}s")
    print(f"  Successful: {len(results)}/{len(symbols)}")
    
    if results:
        print("\n  Sample data (first 2 rows each):")
        for key, df in list(results.items())[:3]:
            print(f"\n  {key}:")
            print(df.head(2).to_string())
    
    return results


def main():
    """Run all demos."""
    print_header("XnoxsFetcher v4.0 - New Features Demo")
    
    print("  This demo showcases the new features:")
    print("  1. Auth Manager - Session persistence & token refresh")
    print("  2. Data Export - CSV, Excel, JSON export")
    print("  3. Parallel Fetch - Multi-symbol concurrent fetching")
    
    demo_auth_manager()
    
    fetcher = XnoxsFetcher()
    data = fetcher.get_historical_data("AAPL", "NASDAQ", TimeFrame.DAILY, 20)
    demo_export(data)
    
    demo_parallel()
    
    print_header("Demo Complete!")
    print("  All new features demonstrated successfully.")
    print("  Check the 'exports' folder for exported files.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

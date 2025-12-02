# XnoxsFetcher v4.0 - TradingView Data Fetcher

## Overview
XnoxsFetcher is a Python library for fetching historical and live market data from TradingView. It supports multiple asset classes including stocks, cryptocurrencies, forex, and commodities from various exchanges worldwide.

**Version:** 4.0.0  
**Author:** developerxnoxs  
**License:** MIT

## Project Structure
```
.
├── xnoxs_fetcher/              # Main library package
│   ├── __init__.py             # Package exports
│   ├── core.py                 # Core XnoxsFetcher class
│   ├── live_feed.py            # Real-time data streaming
│   ├── models.py               # Data models (SymbolSet, DataConsumer)
│   ├── auth.py                 # Authentication manager
│   ├── export.py               # CSV/Excel/JSON export
│   ├── websocket_manager.py    # WebSocket with auto-reconnect
│   ├── parallel.py             # Parallel multi-symbol fetching
│   └── py.typed                # PEP 561 type hints marker
├── tests/                      # Unit tests
│   ├── conftest.py             # Pytest fixtures
│   ├── test_core.py            # Core functionality tests
│   ├── test_auth.py            # Auth manager tests
│   ├── test_export.py          # Export tests
│   └── test_parallel.py        # Parallel fetch tests
├── .github/                    # GitHub configuration
│   ├── workflows/ci.yml        # CI/CD pipeline
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
├── demo.py                     # Basic demonstration script
├── demo_features.py            # New features demo
├── pyproject.toml              # Modern Python packaging (primary)
├── setup.py                    # Legacy compatibility
├── requirements.txt            # Python dependencies
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guidelines
├── CODE_OF_CONDUCT.md          # Community guidelines
├── SECURITY.md                 # Security policy
├── README.md                   # Project documentation
└── LICENSE                     # MIT License
```

## Features in v4.0

### 1. Auth Manager (`auth.py`)
Robust session management with:
- Session persistence to file
- Automatic token refresh
- Rate limiting protection
- Retry with exponential backoff

```python
from xnoxs_fetcher import AuthManager

auth = AuthManager()
token = auth.authenticate("email@example.com", "password")
print(auth.get_session_info())
```

### 2. Data Export (`export.py`)
Export data to multiple formats:
- CSV export
- Excel (.xlsx) export
- JSON export
- Parquet (for large datasets)
- Summary reports

```python
from xnoxs_fetcher import DataExporter

exporter = DataExporter()
exporter.to_csv(data, "AAPL_daily")
exporter.to_excel(data, "portfolio")
exporter.to_json(data, "data")
```

### 3. WebSocket Manager (`websocket_manager.py`)
Robust WebSocket with:
- Auto-reconnect with exponential backoff
- Heartbeat/ping mechanism
- Connection state tracking
- Event callbacks

### 4. Parallel Fetcher (`parallel.py`)
Concurrent multi-symbol fetching:
- Thread pool execution
- Progress callbacks
- Error handling & retry

```python
from xnoxs_fetcher import fetch_parallel, TimeFrame

symbols = [("AAPL", "NASDAQ"), ("GOOGL", "NASDAQ"), ("MSFT", "NASDAQ")]
results = fetch_parallel(fetcher, symbols, TimeFrame.DAILY, bars=100)
```

## Running the Project

### Run Features Demo
```bash
python demo_features.py
```

### Run Basic Demo
```bash
python demo.py
```

### Run Tests
```bash
pytest tests/ -v
```

### Build Package
```bash
python -m build
```

## Basic Usage

```python
from xnoxs_fetcher import XnoxsFetcher, TimeFrame

# Initialize fetcher (anonymous mode)
fetcher = XnoxsFetcher()

# Fetch historical data
data = fetcher.get_hist(
    symbol="AAPL",
    exchange="NASDAQ",
    interval=TimeFrame.DAILY,
    n_bars=100
)

print(data)
```

### Using with Authentication
```python
fetcher = XnoxsFetcher(
    username="your_tradingview_email@example.com",
    password="your_password"
)
```

### Live Data Streaming
```python
from xnoxs_fetcher import XnoxsLiveFeed, TimeFrame

live = XnoxsLiveFeed()
seis = live.create_symbol_set("BTCUSD", "BINANCE", TimeFrame.MINUTE_1)

def on_update(symbol_set, data):
    print(f"BTC: ${data['close'].iloc[0]:,.2f}")

consumer = seis.create_consumer(on_update)
```

## Key Features
- **Multiple Asset Classes:** Stocks, crypto, forex, commodities
- **Global Exchanges:** NASDAQ, NYSE, Binance, IDX, NSE, BSE, and more
- **Flexible Timeframes:** From 1-minute to monthly charts
- **Real-time Streaming:** Live data with callback-based consumers
- **Pandas Integration:** Returns data as Pandas DataFrames
- **Session Persistence:** Save and restore login sessions
- **Multi-format Export:** CSV, Excel, JSON, Parquet
- **Parallel Fetching:** Concurrent multi-symbol data retrieval
- **Auto-reconnect:** Robust WebSocket connection management
- **Cross-Platform:** Windows, macOS, Linux support

## Supported Timeframes
- Minutes: 1, 3, 5, 15, 30, 45
- Hours: 1, 2, 3, 4
- Days+: Daily, Weekly, Monthly

## Dependencies
- pandas >= 2.0.0
- websocket-client >= 1.0.0
- requests >= 2.25.0
- python-dateutil >= 2.8.0
- openpyxl >= 3.1.0 (Excel export)
- pyarrow >= 14.0.0 (Parquet export)

## Environment Variables
- `TRADINGVIEW_USERNAME` - TradingView email
- `TRADINGVIEW_PASSWORD` - TradingView password

## Recent Changes
- December 2, 2025: Professional GitHub Structure
  - Added comprehensive GitHub project files
  - Added CI/CD workflow with GitHub Actions
  - Added unit tests with pytest
  - Added py.typed for PEP 561 compliance
  - Added CHANGELOG, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY
  - Updated pyproject.toml with full tool configuration
- December 2, 2025: Removed Data Cache feature
  - Removed cache.py module
  - Simplified parallel fetcher
- December 2, 2025: v4.0 Major Update
  - Added AuthManager for robust session management
  - Added DataExporter for multi-format export
  - Added WebSocketManager with auto-reconnect
  - Added ParallelFetcher for concurrent requests

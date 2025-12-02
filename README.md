# XnoxsFetcher

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v4.0.0-blue)](https://pypi.org/project/xnoxs_fetcher/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> Advanced TradingView Data Fetcher for Python - Fetch historical and live market data for stocks, crypto, forex, and commodities.

## Apa itu XnoxsFetcher?

**XnoxsFetcher** adalah library Python yang memungkinkan Anda mengambil data pasar keuangan (saham, crypto, forex, komoditas) dari TradingView secara otomatis. Dengan library ini, Anda bisa mendapatkan data harga historis dan data real-time untuk analisis trading atau pembuatan bot trading.

**Author:** developerxnoxs  
**Versi:** 4.0.0  
**Lisensi:** MIT

---

## Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| **Multi-Asset Support** | Saham, Crypto, Forex, Komoditas dari berbagai exchange |
| **Auth Manager** | Login dengan session persistence, auto token refresh |
| **Data Export** | Export ke CSV, Excel, JSON, Parquet |
| **Parallel Fetch** | Ambil banyak simbol sekaligus, 5 simbol dalam ~1 detik |
| **WebSocket Manager** | Auto-reconnect, heartbeat monitoring |
| **Cross-Platform** | Windows, macOS, Linux |

---

## Daftar Isi

1. [Instalasi](#instalasi)
2. [Quick Start](#quick-start)
3. [Fitur v4.0](#fitur-v40)
   - [Auth Manager](#1-auth-manager)
   - [Data Export](#2-data-export)
   - [Parallel Fetch](#3-parallel-fetch)
4. [Mengambil Data](#mengambil-data)
   - [Data Saham](#data-saham)
   - [Data Cryptocurrency](#data-cryptocurrency)
   - [Data Forex](#data-forex)
5. [Timeframe](#timeframe)
6. [Live Data Streaming](#live-data-streaming)
7. [Daftar Exchange](#daftar-exchange)
8. [Development](#development)
9. [Contributing](#contributing)
10. [License](#license)

---

## Instalasi

### Requirements

- Python 3.9+
- pip atau uv package manager

### Install via pip

```bash
pip install git+https://github.com/developerxnoxs/xnoxs_fetcher.git
```

### Install via clone

```bash
git clone https://github.com/developerxnoxs/xnoxs_fetcher.git
cd xnoxs_fetcher
pip install -e .
```

### Install dengan export dependencies

```bash
pip install -e ".[export]"  # Untuk CSV, Excel, Parquet export
```

### Verifikasi Instalasi

```python
from xnoxs_fetcher import XnoxsFetcher, TimeFrame
print("Instalasi berhasil!")
```

---

## Quick Start

```python
from xnoxs_fetcher import XnoxsFetcher, TimeFrame

# Buat instance fetcher
fetcher = XnoxsFetcher()

# Ambil data harian Apple
data = fetcher.get_hist(
    symbol="AAPL",
    exchange="NASDAQ",
    interval=TimeFrame.D1,
    n_bars=100
)

print(data)
```

**Output:**
```
                          symbol     open    high       low   close      volume
datetime                                                                       
2025-11-17 14:30:00  NASDAQ:AAPL  268.815  270.49  265.7300  267.46  45018260.0
2025-11-18 14:30:00  NASDAQ:AAPL  269.990  270.71  265.3200  267.44  45677278.0
...
```

---

## Fitur v4.0

### 1. Auth Manager

Manajemen session yang robust dengan fitur:
- Session persistence (simpan ke file)
- Auto token refresh
- Rate limit protection

```python
from xnoxs_fetcher import AuthManager

auth = AuthManager()
token = auth.authenticate("email@example.com", "password")

if token:
    info = auth.get_session_info()
    print(f"Username: {info['username']}")
    print(f"Expired: {info['is_expired']}")
```

### 2. Data Export

Export data ke berbagai format:

```python
from xnoxs_fetcher import XnoxsFetcher, DataExporter, TimeFrame

fetcher = XnoxsFetcher()
data = fetcher.get_hist("AAPL", "NASDAQ", TimeFrame.D1, 100)

exporter = DataExporter(output_dir="exports")
exporter.to_csv(data, "AAPL_daily")
exporter.to_excel(data, "AAPL_daily")
exporter.to_json(data, "AAPL_daily")
exporter.create_report(data, "AAPL_report")
```

### 3. Parallel Fetch

Ambil data banyak simbol secara bersamaan:

```python
from xnoxs_fetcher import XnoxsFetcher, fetch_parallel, TimeFrame

fetcher = XnoxsFetcher()

symbols = [
    ("AAPL", "NASDAQ"),
    ("GOOGL", "NASDAQ"),
    ("MSFT", "NASDAQ"),
    ("AMZN", "NASDAQ"),
    ("META", "NASDAQ"),
]

results = fetch_parallel(
    fetcher=fetcher,
    symbols=symbols,
    timeframe=TimeFrame.D1,
    bars=100,
    max_workers=5
)

for key, data in results.items():
    symbol, exchange = key
    if data is not None:
        print(f"{symbol}: {len(data)} rows")
```

---

## Mengambil Data

### Data Saham

```python
# Saham Amerika
apple = fetcher.get_hist("AAPL", "NASDAQ", TimeFrame.D1, 100)
tesla = fetcher.get_hist("TSLA", "NASDAQ", TimeFrame.H1, 50)

# Saham Indonesia
bbca = fetcher.get_hist("BBCA", "IDX", TimeFrame.D1, 100)
tlkm = fetcher.get_hist("TLKM", "IDX", TimeFrame.D1, 100)

# Saham India
reliance = fetcher.get_hist("RELIANCE", "NSE", TimeFrame.D1, 100)
```

### Data Cryptocurrency

```python
# Bitcoin
btc = fetcher.get_hist("BTCUSD", "BINANCE", TimeFrame.H1, 500)

# Ethereum
eth = fetcher.get_hist("ETHUSDT", "BINANCE", TimeFrame.M15, 1000)

# Altcoins
sol = fetcher.get_hist("SOLUSDT", "BINANCE", TimeFrame.H4, 200)
```

### Data Forex

```python
eurusd = fetcher.get_hist("EURUSD", "FX", TimeFrame.H1, 500)
gbpusd = fetcher.get_hist("GBPUSD", "FX", TimeFrame.D1, 200)
```

---

## Timeframe

| Kategori | TimeFrame | Penjelasan |
|----------|-----------|------------|
| **Menit** | `TimeFrame.M1` | 1 menit |
| | `TimeFrame.M5` | 5 menit |
| | `TimeFrame.M15` | 15 menit |
| | `TimeFrame.M30` | 30 menit |
| **Jam** | `TimeFrame.H1` | 1 jam |
| | `TimeFrame.H4` | 4 jam |
| **Harian+** | `TimeFrame.D1` | 1 hari |
| | `TimeFrame.W1` | 1 minggu |
| | `TimeFrame.MN` | 1 bulan |

---

## Live Data Streaming

```python
from xnoxs_fetcher import XnoxsLiveFeed, TimeFrame

live = XnoxsLiveFeed()

seis = live.create_symbol_set(
    symbol="BTCUSD",
    exchange="BINANCE",
    interval=TimeFrame.M1
)

def on_new_price(symbol_set, data):
    print(f"BTC: ${data['close'].iloc[0]:,.2f}")

consumer = seis.create_consumer(on_new_price)

# Streaming berjalan di background
# Panggil live.shutdown() untuk menghentikan
```

---

## Daftar Exchange

### Saham
| Exchange | Kode | Contoh |
|----------|------|--------|
| NASDAQ | `NASDAQ` | AAPL, TSLA, MSFT |
| NYSE | `NYSE` | JPM, BAC, WMT |
| Indonesia | `IDX` | BBCA, TLKM, BBRI |
| India NSE | `NSE` | RELIANCE, TCS |
| Hong Kong | `HKEX` | 0700, 9988 |

### Cryptocurrency
| Exchange | Kode | Contoh |
|----------|------|--------|
| Binance | `BINANCE` | BTCUSD, ETHUSDT |
| Coinbase | `COINBASE` | BTCUSD, ETHUSD |
| Bybit | `BYBIT` | BTCUSDT |

### Forex & Komoditas
| Exchange | Kode | Contoh |
|----------|------|--------|
| FX | `FX` | EURUSD, GBPUSD |
| MCX | `MCX` | GOLD, SILVER |
| COMEX | `COMEX` | GC1!, SI1! |

---

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/developerxnoxs/xnoxs_fetcher.git
cd xnoxs_fetcher

# Install dengan dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linter
ruff check .

# Run formatter
ruff format .

# Type checking
mypy xnoxs_fetcher/
```

### Project Structure

```
xnoxs_fetcher/
├── xnoxs_fetcher/          # Main package
│   ├── __init__.py
│   ├── core.py             # Core fetcher
│   ├── auth.py             # Authentication
│   ├── export.py           # Data export
│   ├── parallel.py         # Parallel fetching
│   ├── live_feed.py        # Live streaming
│   ├── websocket_manager.py
│   ├── models.py
│   └── py.typed            # PEP 561 marker
├── tests/                  # Unit tests
├── .github/                # GitHub configs
│   ├── workflows/ci.yml
│   └── ISSUE_TEMPLATE/
├── pyproject.toml          # Modern Python config
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── LICENSE
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/developerxnoxs/xnoxs_fetcher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/developerxnoxs/xnoxs_fetcher/discussions)
- **Security**: See [SECURITY.md](SECURITY.md)

---

Made with ❤️ by [developerxnoxs](https://github.com/developerxnoxs)

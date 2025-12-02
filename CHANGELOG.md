# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [4.0.0] - 2024-12-02

### Added
- **AuthManager**: Robust session management with token refresh and persistence
- **DataExporter**: Multi-format export support (CSV, JSON, Excel, Parquet)
- **WebSocketManager**: Connection pooling with auto-reconnect capability
- **ParallelFetcher**: Concurrent multi-symbol data fetching
- **BatchExporter**: Export multiple datasets in parallel
- Type hints throughout the codebase
- `py.typed` marker for PEP 561 compliance
- Comprehensive GitHub project structure
- GitHub Actions CI/CD workflow
- Professional documentation templates

### Changed
- Updated minimum Python version to 3.9
- Improved WebSocket connection stability
- Enhanced error handling and logging
- Updated login headers to match browser requests
- Modernized packaging with pyproject.toml

### Removed
- **DataCache**: Removed SQLite-based caching system for simpler architecture

### Fixed
- WebSocket reconnection issues
- Session persistence across restarts
- Rate limiting for API requests

## [3.0.0] - 2024-11-15

### Added
- Real-time data streaming via WebSocket
- Multi-exchange support (NASDAQ, NYSE, BINANCE, etc.)
- Callback-based data consumers
- Symbol set management

### Changed
- Refactored core fetcher architecture
- Improved DataFrame handling

## [2.0.0] - 2024-10-01

### Added
- Historical data fetching with multiple timeframes
- Support for stocks, crypto, forex, and commodities
- Pandas DataFrame output

### Changed
- Complete rewrite of the library

## [1.0.0] - 2024-08-01

### Added
- Initial release
- Basic TradingView data fetching
- Simple API interface

[Unreleased]: https://github.com/developerxnoxs/xnoxs_fetcher/compare/v4.0.0...HEAD
[4.0.0]: https://github.com/developerxnoxs/xnoxs_fetcher/compare/v3.0.0...v4.0.0
[3.0.0]: https://github.com/developerxnoxs/xnoxs_fetcher/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/developerxnoxs/xnoxs_fetcher/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/developerxnoxs/xnoxs_fetcher/releases/tag/v1.0.0

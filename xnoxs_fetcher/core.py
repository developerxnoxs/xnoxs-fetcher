"""
XnoxsFetcher Core Module

This module contains the main XnoxsFetcher class for retrieving
historical market data from TradingView.

Author: developerxnoxs
"""

from __future__ import annotations

import datetime
import enum
import json
import logging
import random
import re
import string
from dataclasses import dataclass, field
from typing import Optional, Any, Dict, List, Union

import pandas as pd
import requests
from websocket import create_connection, WebSocket

logger = logging.getLogger(__name__)


class TimeFrame(enum.Enum):
    """
    Enumeration of supported chart timeframes.
    
    Each value represents the interval string used by TradingView's API.
    """
    MINUTE_1 = "1"
    MINUTE_3 = "3"
    MINUTE_5 = "5"
    MINUTE_15 = "15"
    MINUTE_30 = "30"
    MINUTE_45 = "45"
    HOUR_1 = "1H"
    HOUR_2 = "2H"
    HOUR_3 = "3H"
    HOUR_4 = "4H"
    DAILY = "1D"
    WEEKLY = "1W"
    MONTHLY = "1M"
    
    @classmethod
    def from_string(cls, value: str) -> "TimeFrame":
        """
        Convert a string representation to TimeFrame enum.
        
        Args:
            value: String representation of timeframe
            
        Returns:
            Corresponding TimeFrame enum value
            
        Raises:
            ValueError: If no matching timeframe found
        """
        mapping = {
            "1": cls.MINUTE_1, "1m": cls.MINUTE_1,
            "3": cls.MINUTE_3, "3m": cls.MINUTE_3,
            "5": cls.MINUTE_5, "5m": cls.MINUTE_5,
            "15": cls.MINUTE_15, "15m": cls.MINUTE_15,
            "30": cls.MINUTE_30, "30m": cls.MINUTE_30,
            "45": cls.MINUTE_45, "45m": cls.MINUTE_45,
            "1h": cls.HOUR_1, "1H": cls.HOUR_1,
            "2h": cls.HOUR_2, "2H": cls.HOUR_2,
            "3h": cls.HOUR_3, "3H": cls.HOUR_3,
            "4h": cls.HOUR_4, "4H": cls.HOUR_4,
            "1d": cls.DAILY, "1D": cls.DAILY, "d": cls.DAILY,
            "1w": cls.WEEKLY, "1W": cls.WEEKLY, "w": cls.WEEKLY,
            "1M": cls.MONTHLY, "M": cls.MONTHLY,
        }
        if value in mapping:
            return mapping[value]
        raise ValueError(f"Unknown timeframe: {value}")


@dataclass
class FetcherConfig:
    """Configuration for XnoxsFetcher."""
    ws_timeout: int = 5
    ws_debug: bool = False
    sign_in_url: str = "https://www.tradingview.com/accounts/signin/"
    search_url: str = "https://symbol-search.tradingview.com/symbol_search/?text={}&hl=1&exchange={}&lang=en&type=&domain=production"
    ws_origin: str = "https://data.tradingview.com"
    ws_endpoint: str = "wss://data.tradingview.com/socket.io/websocket"


class XnoxsFetcher:
    """
    Advanced TradingView Historical Data Fetcher.
    
    This class provides methods to authenticate with TradingView,
    search for symbols, and retrieve historical OHLCV data.
    
    Attributes:
        token: Authentication token for TradingView API
        session: WebSocket session identifier
        chart_session: Chart session identifier
        
    Example:
        >>> fetcher = XnoxsFetcher()
        >>> data = fetcher.get_historical_data("AAPL", "NASDAQ", TimeFrame.DAILY, 100)
        >>> print(data.head())
    
    Author: developerxnoxs
    """
    
    __slots__ = (
        "_config", "_token", "_ws", "_session", 
        "_chart_session", "_ws_debug"
    )
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        config: Optional[FetcherConfig] = None
    ) -> None:
        """
        Initialize XnoxsFetcher instance.
        
        Args:
            username: TradingView account username (optional)
            password: TradingView account password (optional)  
            config: Custom configuration (optional)
        """
        self._config = config or FetcherConfig()
        self._ws_debug = self._config.ws_debug
        self._ws: Optional[WebSocket] = None
        
        self._token = self._authenticate(username, password)
        
        if self._token is None:
            self._token = "unauthorized_user_token"
            logger.warning(
                "Using anonymous mode - data access may be limited"
            )
        
        self._session = self._create_session_id()
        self._chart_session = self._create_chart_session_id()
    
    @property
    def token(self) -> str:
        """Get authentication token."""
        return self._token
    
    @property
    def session(self) -> str:
        """Get session identifier."""
        return self._session
    
    @property
    def chart_session(self) -> str:
        """Get chart session identifier."""
        return self._chart_session
    
    @property
    def ws_debug(self) -> bool:
        """Get WebSocket debug mode status."""
        return self._ws_debug
    
    @ws_debug.setter 
    def ws_debug(self, value: bool) -> None:
        """Set WebSocket debug mode."""
        self._ws_debug = value
    
    def _authenticate(
        self, 
        username: Optional[str], 
        password: Optional[str]
    ) -> Optional[str]:
        """
        Authenticate with TradingView.
        
        Args:
            username: TradingView username
            password: TradingView password
            
        Returns:
            Authentication token or None if failed
        """
        if username is None or password is None:
            return None
        
        headers = {
            "Host": "www.tradingview.com",
            "Origin": "https://www.tradingview.com",
            "Referer": "https://www.tradingview.com/",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7444.102 Mobile Safari/537.36",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "id,id-ID;q=0.9,en-US;q=0.8,en;q=0.7",
            "x-language": "en",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua": '"Chromium";v="142", "Android WebView";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "same-origin",
            "sec-fetch-site": "same-origin",
        }
        
        files = {
            "username": (None, username),
            "password": (None, password),
            "remember": (None, "true"),
        }
        
        try:
            session = requests.Session()
            
            session.cookies.set("cookiePrivacyPreferenceBannerProduction", "notApplicable", domain=".tradingview.com")
            session.cookies.set("cookiesSettings", '{"analytics":true,"advertising":true}', domain=".tradingview.com")
            
            response = session.post(
                self._config.sign_in_url,
                files=files,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("error"):
                logger.error(f"Login error: {result['error']}")
                return None
            
            user_data = result.get("user", {})
            
            if "auth_token" in user_data:
                logger.info(f"Login successful for user: {user_data.get('username')}")
                return user_data["auth_token"]
            
            if "sessionid" in session.cookies:
                logger.info(f"Login successful (session-based) for user: {user_data.get('username')}")
                return session.cookies.get("sessionid")
            
            logger.warning("Login succeeded but no auth token found, using session cookies")
            return f"session:{session.cookies.get('sessionid', 'unknown')}"
            
        except requests.exceptions.RequestException as exc:
            logger.error(f"Authentication request failed: {exc}")
            return None
        except (KeyError, ValueError) as exc:
            logger.error(f"Authentication failed to parse response: {exc}")
            return None
    
    def _establish_websocket(self) -> None:
        """Establish WebSocket connection to TradingView."""
        logger.debug("Establishing WebSocket connection...")
        ws_headers = json.dumps({"Origin": self._config.ws_origin})
        self._ws = create_connection(
            self._config.ws_endpoint,
            headers=ws_headers,
            timeout=self._config.ws_timeout
        )
    
    @staticmethod
    def _create_session_id(length: int = 12) -> str:
        """Generate a random session identifier."""
        chars = string.ascii_lowercase
        random_part = "".join(random.choice(chars) for _ in range(length))
        return f"qs_{random_part}"
    
    @staticmethod
    def _create_chart_session_id(length: int = 12) -> str:
        """Generate a random chart session identifier."""
        chars = string.ascii_lowercase
        random_part = "".join(random.choice(chars) for _ in range(length))
        return f"cs_{random_part}"
    
    @staticmethod
    def _add_header(message: str) -> str:
        """Add TradingView message header."""
        return f"~m~{len(message)}~m~{message}"
    
    @staticmethod
    def _build_message(func_name: str, params: List[Any]) -> str:
        """Build JSON message for WebSocket."""
        return json.dumps({"m": func_name, "p": params}, separators=(",", ":"))
    
    def _create_ws_message(self, func_name: str, params: List[Any]) -> str:
        """Create complete WebSocket message with header."""
        return self._add_header(self._build_message(func_name, params))
    
    def _send_ws_message(self, func_name: str, params: List[Any]) -> None:
        """Send message through WebSocket."""
        message = self._create_ws_message(func_name, params)
        if self._ws_debug:
            print(f"[DEBUG] Sending: {message}")
        self._ws.send(message)
    
    @staticmethod
    def _parse_raw_data(raw_data: str, symbol: str) -> Optional[pd.DataFrame]:
        """
        Parse raw WebSocket response into DataFrame.
        
        Args:
            raw_data: Raw response string from WebSocket
            symbol: Symbol name for labeling
            
        Returns:
            DataFrame with OHLCV data or None if parsing failed
        """
        try:
            match = re.search(r'"s":\[(.+?)\}\]', raw_data)
            if not match:
                return None
                
            data_str = match.group(1)
            rows = data_str.split(',{"')
            parsed_data: List[List[Any]] = []
            has_volume = True
            
            for row in rows:
                parts = re.split(r"\[|:|,|\]", row)
                timestamp = datetime.datetime.fromtimestamp(float(parts[4]))
                
                record = [timestamp]
                for idx in range(5, 10):
                    if not has_volume and idx == 9:
                        record.append(0.0)
                        continue
                    try:
                        record.append(float(parts[idx]))
                    except (ValueError, IndexError):
                        has_volume = False
                        record.append(0.0)
                        logger.debug("Volume data not available")
                
                parsed_data.append(record)
            
            df = pd.DataFrame(
                parsed_data,
                columns=["datetime", "open", "high", "low", "close", "volume"]
            ).set_index("datetime")
            df.insert(0, "symbol", symbol)
            
            return df
            
        except AttributeError:
            logger.error("Failed to parse data - check symbol and exchange")
            return None
    
    @staticmethod
    def _format_symbol(
        symbol: str, 
        exchange: str, 
        contract: Optional[int] = None
    ) -> str:
        """
        Format symbol string for TradingView API.
        
        Args:
            symbol: Raw symbol name
            exchange: Exchange name
            contract: Futures contract number (optional)
            
        Returns:
            Formatted symbol string
        """
        if ":" in symbol:
            return symbol
            
        if contract is None:
            return f"{exchange}:{symbol}"
        
        if isinstance(contract, int):
            return f"{exchange}:{symbol}{contract}!"
            
        raise ValueError(f"Invalid contract value: {contract}")
    
    def get_historical_data(
        self,
        symbol: str,
        exchange: str = "NSE",
        timeframe: TimeFrame = TimeFrame.DAILY,
        bars: int = 10,
        futures_contract: Optional[int] = None,
        extended_session: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        Retrieve historical OHLCV data from TradingView.
        
        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTCUSD")
            exchange: Exchange name (e.g., "NASDAQ", "BINANCE")
            timeframe: Chart timeframe (default: DAILY)
            bars: Number of bars to retrieve (max: 5000)
            futures_contract: Futures contract number (optional)
                - None: Spot/cash
                - 1: Current front month
                - 2: Next front month
            extended_session: Include extended trading hours
            
        Returns:
            DataFrame with columns: symbol, open, high, low, close, volume
            Returns None if data retrieval fails
            
        Example:
            >>> fetcher = XnoxsFetcher()
            >>> data = fetcher.get_historical_data(
            ...     "AAPL", "NASDAQ", TimeFrame.HOUR_1, 100
            ... )
        """
        formatted_symbol = self._format_symbol(
            symbol, exchange, futures_contract
        )
        interval_value = timeframe.value
        
        self._establish_websocket()
        
        self._send_ws_message("set_auth_token", [self._token])
        self._send_ws_message("chart_create_session", [self._chart_session, ""])
        self._send_ws_message("quote_create_session", [self._session])
        
        quote_fields = [
            self._session,
            "ch", "chp", "current_session", "description", "local_description",
            "language", "exchange", "fractional", "is_tradable", "lp", "lp_time",
            "minmov", "minmove2", "original_name", "pricescale", "pro_name",
            "short_name", "type", "update_mode", "volume", "currency_code",
            "rchp", "rtc",
        ]
        self._send_ws_message("quote_set_fields", quote_fields)
        
        self._send_ws_message(
            "quote_add_symbols",
            [self._session, formatted_symbol, {"flags": ["force_permission"]}]
        )
        self._send_ws_message("quote_fast_symbols", [self._session, formatted_symbol])
        
        session_type = '"extended"' if extended_session else '"regular"'
        resolve_payload = (
            f'={{"symbol":"{formatted_symbol}",'
            f'"adjustment":"splits","session":{session_type}}}'
        )
        self._send_ws_message(
            "resolve_symbol",
            [self._chart_session, "symbol_1", resolve_payload]
        )
        
        self._send_ws_message(
            "create_series",
            [self._chart_session, "s1", "s1", "symbol_1", interval_value, bars]
        )
        self._send_ws_message("switch_timezone", [self._chart_session, "exchange"])
        
        raw_data = ""
        logger.debug(f"Fetching data for {formatted_symbol}...")
        
        while True:
            try:
                result = self._ws.recv()
                raw_data += result + "\n"
            except Exception as exc:
                logger.error(f"WebSocket error: {exc}")
                break
            
            if "series_completed" in result:
                break
        
        return self._parse_raw_data(raw_data, formatted_symbol)
    
    def search_symbols(
        self, 
        query: str, 
        exchange: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Search for trading symbols on TradingView.
        
        Args:
            query: Search query (e.g., "AAPL", "Bitcoin")
            exchange: Filter by exchange (optional)
            
        Returns:
            List of matching symbol dictionaries
            
        Example:
            >>> fetcher = XnoxsFetcher()
            >>> results = fetcher.search_symbols("AAPL", "NASDAQ")
            >>> for r in results[:3]:
            ...     print(f"{r['symbol']} - {r['description']}")
        """
        url = self._config.search_url.format(query, exchange)
        
        headers = {
            "Referer": "https://www.tradingview.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 403:
                logger.warning("Symbol search blocked by TradingView - try again later")
                return []
                
            response.raise_for_status()
            
            text = response.text.replace("</em>", "").replace("<em>", "")
            return json.loads(text)
            
        except requests.exceptions.HTTPError as exc:
            logger.warning(f"Symbol search HTTP error: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Symbol search failed: {exc}")
            return []
    
    def search_symbol(
        self,
        text: str,
        exchange: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Search for trading symbols (backward compatibility alias).
        
        See search_symbols() for full documentation.
        """
        return self.search_symbols(text, exchange)
    
    def get_hist(
        self,
        symbol: str,
        exchange: str = "NSE",
        interval: "TimeFrame" = None,
        n_bars: int = 10,
        fut_contract: Optional[int] = None,
        extended_session: bool = False,
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data (backward compatibility alias).
        
        See get_historical_data() for full documentation.
        """
        if interval is None:
            interval = TimeFrame.DAILY
        return self.get_historical_data(
            symbol=symbol,
            exchange=exchange,
            timeframe=interval,
            bars=n_bars,
            futures_contract=fut_contract,
            extended_session=extended_session,
        )


# Backward compatibility aliases
Interval = TimeFrame
TvDatafeed = XnoxsFetcher


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    fetcher = XnoxsFetcher()
    
    print("\n=== Crude Oil Futures ===")
    print(fetcher.get_historical_data("CRUDEOIL", "MCX", futures_contract=1))
    
    print("\n=== Nifty Futures ===")
    print(fetcher.get_historical_data("NIFTY", "NSE", futures_contract=1))
    
    print("\n=== Eicher Motors Hourly ===")
    print(fetcher.get_historical_data(
        "EICHERMOT", "NSE",
        timeframe=TimeFrame.HOUR_1,
        bars=500,
        extended_session=False
    ))

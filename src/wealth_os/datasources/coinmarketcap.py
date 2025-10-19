from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

import requests

import os

from .base import OHLCVPoint, PriceQuote
from .registry import register_price_source


class _CMCClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        # Normalize base URL: ensure scheme and strip trailing slash
        if "://" not in base_url:
            base_url = "https://" + base_url
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Accepts": "application/json",
                "X-CMC_PRO_API_KEY": api_key,
                "User-Agent": "wealth-cli/0.1",
            }
        )

    def get(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params, timeout=30)
        if r.status_code == 429:
            raise RuntimeError("CoinMarketCap rate limit exceeded (HTTP 429)")
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # Try to extract CMC error payload for clarity
            err_detail = None
            try:
                j = r.json()
                status = j.get("status", {})
                code = status.get("error_code")
                msg = status.get("error_message")
                if code or msg:
                    err_detail = f"CMC error {code}: {msg}"
            except Exception:
                pass
            if err_detail:
                raise RuntimeError(
                    f"HTTP {r.status_code} from {url}: {err_detail}"
                ) from e
            raise
        data = r.json()
        status = data.get("status", {})
        if status.get("error_code") not in (None, 0):
            raise RuntimeError(
                f"CoinMarketCap error {status.get('error_code')}: {status.get('error_message')}"
            )
        return data

    def map_symbol(self, symbol: str) -> Optional[int]:
        resp = self.get("/v1/cryptocurrency/map", params={"symbol": symbol.upper()})
        items = resp.get("data") or []
        for item in items:
            if item.get("symbol") == symbol.upper():
                return int(item.get("id"))
        return None

    def quotes_latest(self, symbol: str, convert: str = "USD") -> PriceQuote:
        resp = self.get(
            "/v2/cryptocurrency/quotes/latest",
            params={"symbol": symbol.upper(), "convert": convert.upper()},
        )
        data = resp.get("data", {})
        sym = symbol.upper()
        item = data.get(sym)
        if isinstance(item, list):
            item = item[0] if item else None
        if not item:
            raise RuntimeError(f"No quote data for {sym}")
        quote_data = item.get("quote", {}).get(convert.upper())
        if not quote_data:
            raise RuntimeError(f"No quote pricing for {sym}/{convert}")
        price = Decimal(str(quote_data["price"]))
        ts = datetime.fromisoformat(quote_data["last_updated"].replace("Z", "+00:00"))
        return PriceQuote(
            symbol=symbol.upper(), quote_ccy=convert.upper(), price=price, ts=ts
        )

    def ohlcv_historical(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        *,
        interval: str = "daily",
        convert: str = "USD",
    ) -> List[OHLCVPoint]:
        # CoinMarketCap typically expects 'daily', 'weekly', etc. Map common aliases.
        interval_map = {"1d": "daily", "daily": "daily"}
        interval_param = interval_map.get(interval, interval)

        def _fmt(dt: datetime) -> str:
            # Use second precision, avoid microseconds
            if dt.tzinfo is None:
                return dt.replace(microsecond=0).isoformat()
            return dt.astimezone().replace(microsecond=0).isoformat()

        params = {
            "symbol": symbol.upper(),
            "convert": convert.upper(),
            "time_start": _fmt(start),
            "time_end": _fmt(end),
            "interval": interval_param,
        }
        data = self.get("/v2/cryptocurrency/ohlcv/historical", params=params)
        data_obj = data.get("data", {})
        quotes = data_obj.get("quotes", [])
        out: List[OHLCVPoint] = []
        for q in quotes:
            ts = datetime.fromisoformat(q["time_open"].replace("Z", "+00:00"))
            conv = q.get("quote", {}).get(convert.upper(), {})
            out.append(
                OHLCVPoint(
                    ts=ts,
                    open=Decimal(str(conv.get("open"))),
                    high=Decimal(str(conv.get("high"))),
                    low=Decimal(str(conv.get("low"))),
                    close=Decimal(str(conv.get("close"))),
                    volume=Decimal(str(conv.get("volume")))
                    if conv.get("volume") is not None
                    else None,
                )
            )
        return out


@register_price_source
class CoinMarketCapPriceSource:
    @classmethod
    def id(cls) -> str:
        return "coinmarketcap"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("COINMARKETCAP_API_KEY")
        if not api_key:
            raise RuntimeError("COINMARKETCAP_API_KEY not configured")
        url = base_url or os.getenv(
            "COINMARKETCAP_BASE_URL", "https://sandbox-api.coinmarketcap.com"
        )
        self.client = _CMCClient(api_key, url)
        self._symbol_id_cache: Dict[str, Optional[int]] = {}

    def get_quote(self, symbol: str, quote: str = "USD") -> PriceQuote:
        return self.client.quotes_latest(symbol, convert=quote)

    def get_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        quote: str = "USD",
    ) -> List[OHLCVPoint]:
        interval_alias = "daily" if interval in ("1d", "daily") else interval
        return self.client.ohlcv_historical(
            symbol, start, end, interval=interval_alias, convert=quote
        )

    def resolve_symbol_id(self, symbol: str) -> Optional[str]:
        key = symbol.upper()
        if key in self._symbol_id_cache:
            val = self._symbol_id_cache[key]
        else:
            val = self.client.map_symbol(key)
            self._symbol_id_cache[key] = val
        return str(val) if val is not None else None

from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional

import requests

from .base import OHLCVPoint, PriceQuote
from .registry import register_price_source


class _CDClient:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        base = base_url or os.getenv(
            "COINDESK_BASE_URL", "https://min-api.cryptocompare.com"
        )
        if "://" not in base:
            base = "https://" + base
        self.base_url = base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-type": "application/json; charset=UTF-8",
                "authorization": f"Apikey {api_key}",
                "User-Agent": "wealth-cli/0.1",
            }
        )

    def get(self, path: str, params: Optional[Dict[str, str]] = None) -> dict:
        url = f"{self.base_url}{path}"
        r = self.session.get(url, params=params, timeout=30)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            try:
                j = r.json()
            except Exception:
                j = None
            raise RuntimeError(f"HTTP {r.status_code} from {url}: {j}") from e
        return r.json()

    def price_single(self, fsym: str, tsym: str = "USD") -> PriceQuote:
        data = self.get(
            "/data/price", params={"fsym": fsym.upper(), "tsyms": tsym.upper()}
        )
        key = tsym.upper()
        if key not in data:
            raise RuntimeError(f"No price found for {fsym}/{tsym}: {data}")
        price = Decimal(str(data[key]))
        ts = datetime.now(timezone.utc).replace(tzinfo=None)
        return PriceQuote(
            symbol=fsym.upper(), quote_ccy=tsym.upper(), price=price, ts=ts
        )

    def histoday(
        self, fsym: str, tsym: str, start: datetime, end: datetime
    ) -> List[OHLCVPoint]:
        # CryptoCompare histoday: returns up to 2000 daily points per request, ending at toTs
        max_points = 2000
        out: List[OHLCVPoint] = []
        # normalize to naive UTC
        if start.tzinfo is not None:
            start = start.astimezone(timezone.utc).replace(tzinfo=None)
        if end.tzinfo is not None:
            end = end.astimezone(timezone.utc).replace(tzinfo=None)

        to_ts = int(end.timestamp())
        while True:
            # estimate remaining days
            days = max(0, int((datetime.fromtimestamp(to_ts) - start).days))
            if days <= 0:
                break
            limit = min(max_points, days)
            resp = self.get(
                "/data/v2/histoday",
                params={
                    "fsym": fsym.upper(),
                    "tsym": tsym.upper(),
                    "toTs": to_ts,
                    "limit": limit,
                    "aggregate": 1,
                },
            )
            if resp.get("Response") == "Error":
                raise RuntimeError(f"histoday error: {resp}")
            data = resp.get("Data", {}).get("Data", [])
            if not data:
                break
            # data is ascending by time
            for d in data:
                ts = datetime.utcfromtimestamp(int(d["time"]))
                if ts < start or ts > end:
                    continue
                out.append(
                    OHLCVPoint(
                        ts=ts,
                        open=Decimal(str(d["open"])),
                        high=Decimal(str(d["high"])),
                        low=Decimal(str(d["low"])),
                        close=Decimal(str(d["close"])),
                        volume=Decimal(str(d.get("volumefrom", 0))),
                    )
                )
            # Move window earlier
            earliest = data[0]["time"]
            to_ts = int(earliest) - 1
            if len(data) < limit + 1 and to_ts <= int(start.timestamp()):
                break
        # ensure sorted ascending
        out.sort(key=lambda p: p.ts)
        return out


@register_price_source
class CoindeskLegacyPriceSource:
    @classmethod
    def id(cls) -> str:
        return "coindesk"

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("COINDESK_API_KEY")
        if not api_key:
            raise RuntimeError("COINDESK_API_KEY not configured")
        self.client = _CDClient(api_key, base_url)

    def get_quote(self, symbol: str, quote: str = "USD") -> PriceQuote:
        return self.client.price_single(symbol, tsym=quote)

    def get_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        quote: str = "USD",
    ) -> List[OHLCVPoint]:
        if interval not in ("1d", "daily", "day", "histoday"):
            raise NotImplementedError(
                "Coindesk legacy provider supports daily candles only"
            )
        return self.client.histoday(symbol, quote, start, end)

    def resolve_symbol_id(self, symbol: str) -> Optional[str]:
        return symbol.upper()

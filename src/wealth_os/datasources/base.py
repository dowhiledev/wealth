from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

from wealth_os.db.models import TxSide


class PriceQuote(BaseModel):
    symbol: str
    quote_ccy: str = "USD"
    price: Decimal
    ts: datetime


class OHLCVPoint(BaseModel):
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Optional[Decimal] = None


class NormalizedTx(BaseModel):
    ts: datetime
    account: Optional[str] = None
    asset_symbol: str
    side: TxSide
    qty: Decimal
    price_quote: Optional[Decimal] = None
    total_quote: Optional[Decimal] = None
    quote_ccy: str = "USD"
    fee_qty: Optional[Decimal] = None
    fee_asset: Optional[str] = None
    note: Optional[str] = None
    tx_hash: Optional[str] = None
    external_id: Optional[str] = None
    datasource: Optional[str] = None
    tags: Optional[str] = None


@runtime_checkable
class PriceDataSource(Protocol):
    @classmethod
    def id(cls) -> str:  # e.g., "coinmarketcap"
        ...

    def get_quote(self, symbol: str, quote: str = "USD") -> PriceQuote: ...

    def get_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        interval: str = "1d",
        quote: str = "USD",
    ) -> List[OHLCVPoint]: ...

    def resolve_symbol_id(self, symbol: str) -> Optional[str]:
        """Optional: map symbol to provider-specific ID."""
        ...


@runtime_checkable
class TxImportSource(Protocol):
    @classmethod
    def id(cls) -> str:  # e.g., "generic_csv"
        ...

    @classmethod
    def supports_csv(cls) -> bool:
        return True

    def parse_csv(
        self, path: str, options: Optional[Dict[str, Any]] = None
    ) -> List[NormalizedTx]: ...

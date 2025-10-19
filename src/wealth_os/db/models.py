from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Index, UniqueConstraint, String
from sqlalchemy.dialects.sqlite import NUMERIC
from sqlmodel import Field, SQLModel


class AccountType(str, Enum):
    exchange = "exchange"
    wallet = "wallet"


class TxSide(str, Enum):
    buy = "buy"
    sell = "sell"
    transfer_in = "transfer_in"
    transfer_out = "transfer_out"
    stake = "stake"
    reward = "reward"
    fee = "fee"


class Asset(SQLModel, table=True):
    symbol: str = Field(primary_key=True, index=True)
    name: Optional[str] = Field(default=None)
    type: str = Field(default="crypto", index=True)
    decimals: int = Field(default=18)
    cmc_id: Optional[int] = Field(default=None, index=True)

    # Relationships omitted for simplicity in v1


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: AccountType = Field(
        default=AccountType.exchange, sa_column=Column("type", String, nullable=False)
    )
    datasource: Optional[str] = Field(default=None, index=True)
    external_id: Optional[str] = Field(default=None, index=True)
    currency: str = Field(default="USD")
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships omitted for simplicity in v1


class ImportBatch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    datasource: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    source_file: Optional[str] = Field(default=None)
    summary: Optional[str] = Field(default=None)


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(index=True)

    account_id: int = Field(foreign_key="account.id", index=True)
    asset_symbol: str = Field(foreign_key="asset.symbol", index=True)
    side: TxSide = Field(sa_column=Column("side", String, nullable=False))

    qty: Decimal = Field(sa_column=Column(NUMERIC(38, 18)))
    price_quote: Optional[Decimal] = Field(
        default=None, sa_column=Column(NUMERIC(38, 18))
    )
    total_quote: Optional[Decimal] = Field(
        default=None, sa_column=Column(NUMERIC(38, 18))
    )
    quote_ccy: Optional[str] = Field(default="USD", index=True)

    fee_qty: Optional[Decimal] = Field(default=None, sa_column=Column(NUMERIC(38, 18)))
    fee_asset: Optional[str] = Field(default=None, index=True)

    note: Optional[str] = Field(default=None)
    tx_hash: Optional[str] = Field(default=None, index=True)
    external_id: Optional[str] = Field(default=None, index=True)
    datasource: Optional[str] = Field(default=None, index=True)
    import_batch_id: Optional[int] = Field(
        default=None, foreign_key="importbatch.id", index=True
    )
    tags: Optional[str] = Field(default=None, index=True)

    # Relationships omitted for simplicity in v1

    __table_args__ = (Index("ix_tx_account_ts", "account_id", "ts"),)


class Price(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_symbol: str = Field(foreign_key="asset.symbol", index=True)
    quote_ccy: str = Field(default="USD", index=True)
    ts: datetime = Field(index=True)
    price: Decimal = Field(sa_column=Column(NUMERIC(38, 18)))
    source: Optional[str] = Field(default="coinmarketcap", index=True)

    __table_args__ = (
        UniqueConstraint(
            "asset_symbol", "quote_ccy", "ts", name="uq_price_symbol_quote_ts"
        ),
        Index("ix_price_symbol_ts", "asset_symbol", "ts"),
    )


class AssetPreference(SQLModel, table=True):
    asset_symbol: str = Field(primary_key=True, foreign_key="asset.symbol")
    preferred_price_source: Optional[str] = Field(default=None, index=True)

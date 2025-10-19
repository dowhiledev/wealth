from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from .engine import get_engine
from .models import (
    Account,
    AccountType,
    Asset,
    Price,
    Transaction,
    TxSide,
    ImportBatch,
    AssetPreference,
)


@contextmanager
def session_scope(db_path: str):
    engine = get_engine(db_path)
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Asset helpers
def get_asset(session: Session, symbol: str) -> Optional[Asset]:
    return session.get(Asset, symbol)


def ensure_asset(
    session: Session,
    symbol: str,
    *,
    name: Optional[str] = None,
    type_: str = "crypto",
    decimals: int = 18,
    cmc_id: Optional[int] = None,
) -> Asset:
    symbol_u = symbol.upper()
    asset = get_asset(session, symbol_u)
    if asset:
        return asset
    asset = Asset(
        symbol=symbol_u, name=name, type=type_, decimals=decimals, cmc_id=cmc_id
    )
    session.add(asset)
    session.flush()
    return asset


# Account CRUD
def create_account(
    session: Session,
    *,
    name: str,
    type_: AccountType,
    datasource: Optional[str] = None,
    external_id: Optional[str] = None,
    currency: str = "USD",
) -> Account:
    acc = Account(
        name=name,
        type=type_,
        datasource=datasource,
        external_id=external_id,
        currency=currency,
    )
    session.add(acc)
    session.flush()
    return acc


def get_account(session: Session, account_id: int) -> Optional[Account]:
    return session.get(Account, account_id)


def list_accounts(
    session: Session,
    *,
    name_like: Optional[str] = None,
    datasource: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Account]:
    stmt = select(Account)
    if name_like:
        stmt = stmt.where(Account.name.ilike(f"%{name_like}%"))
    if datasource:
        stmt = stmt.where(Account.datasource == datasource)
    stmt = stmt.order_by(Account.created_at.desc()).limit(limit).offset(offset)
    return list(session.exec(stmt))


def delete_account(session: Session, account_id: int) -> bool:
    acc = get_account(session, account_id)
    if not acc:
        return False
    session.delete(acc)
    session.flush()
    return True


def update_account(
    session: Session,
    account_id: int,
    *,
    name: str | None = None,
    type_: AccountType | None = None,
    datasource: str | None = None,
    external_id: str | None = None,
    currency: str | None = None,
) -> Account | None:
    acc = get_account(session, account_id)
    if not acc:
        return None
    if name is not None:
        acc.name = name
    if type_ is not None:
        acc.type = type_
    if datasource is not None:
        acc.datasource = datasource
    if external_id is not None:
        acc.external_id = external_id
    if currency is not None:
        acc.currency = currency
    session.add(acc)
    session.flush()
    return acc


# Transaction CRUD
def create_transaction(
    session: Session,
    *,
    ts: datetime,
    account_id: int,
    asset_symbol: str,
    side: TxSide,
    qty,
    price_quote=None,
    total_quote=None,
    quote_ccy: Optional[str] = "USD",
    fee_qty=None,
    fee_asset: Optional[str] = None,
    note: Optional[str] = None,
    tx_hash: Optional[str] = None,
    external_id: Optional[str] = None,
    datasource: Optional[str] = None,
    import_batch_id: Optional[int] = None,
    tags: Optional[str] = None,
) -> Transaction:
    # Ensure asset exists
    ensure_asset(session, asset_symbol)
    if fee_asset:
        ensure_asset(session, fee_asset)

    tx = Transaction(
        ts=ts,
        account_id=account_id,
        asset_symbol=asset_symbol.upper(),
        side=side,
        qty=qty,
        price_quote=price_quote,
        total_quote=total_quote,
        quote_ccy=quote_ccy,
        fee_qty=fee_qty,
        fee_asset=fee_asset.upper() if fee_asset else None,
        note=note,
        tx_hash=tx_hash,
        external_id=external_id,
        datasource=datasource,
        import_batch_id=import_batch_id,
        tags=tags,
    )
    session.add(tx)
    session.flush()
    return tx


def get_transaction(session: Session, tx_id: int) -> Optional[Transaction]:
    return session.get(Transaction, tx_id)


def list_transactions(
    session: Session,
    *,
    account_id: Optional[int] = None,
    asset_symbol: Optional[str] = None,
    side: Optional[TxSide] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    stmt = select(Transaction)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    if asset_symbol:
        stmt = stmt.where(Transaction.asset_symbol == asset_symbol.upper())
    if side is not None:
        stmt = stmt.where(Transaction.side == side)
    if since is not None:
        stmt = stmt.where(Transaction.ts >= since)
    if until is not None:
        stmt = stmt.where(Transaction.ts <= until)
    stmt = stmt.order_by(Transaction.ts.desc()).limit(limit).offset(offset)
    return list(session.exec(stmt))


def delete_transaction(session: Session, tx_id: int) -> bool:
    tx = get_transaction(session, tx_id)
    if not tx:
        return False
    session.delete(tx)
    session.flush()
    return True


def update_transaction(
    session: Session,
    tx_id: int,
    *,
    ts: datetime | None = None,
    account_id: int | None = None,
    asset_symbol: str | None = None,
    side: TxSide | None = None,
    qty=None,
    price_quote=None,
    total_quote=None,
    quote_ccy: str | None = None,
    fee_qty=None,
    fee_asset: str | None = None,
    note: str | None = None,
    tx_hash: str | None = None,
    external_id: str | None = None,
    datasource: str | None = None,
    import_batch_id: int | None = None,
    tags: str | None = None,
) -> Transaction | None:
    tx = get_transaction(session, tx_id)
    if not tx:
        return None
    if ts is not None:
        tx.ts = ts
    if account_id is not None:
        tx.account_id = account_id
    if asset_symbol is not None:
        ensure_asset(session, asset_symbol)
        tx.asset_symbol = asset_symbol.upper()
    if side is not None:
        tx.side = side
    if qty is not None:
        tx.qty = qty
    if price_quote is not None:
        tx.price_quote = price_quote
    if total_quote is not None:
        tx.total_quote = total_quote
    if quote_ccy is not None:
        tx.quote_ccy = quote_ccy
    if fee_qty is not None:
        tx.fee_qty = fee_qty
    if fee_asset is not None:
        ensure_asset(session, fee_asset)
        tx.fee_asset = fee_asset.upper()
    if note is not None:
        tx.note = note
    if tx_hash is not None:
        tx.tx_hash = tx_hash
    if external_id is not None:
        tx.external_id = external_id
    if datasource is not None:
        tx.datasource = datasource
    if import_batch_id is not None:
        tx.import_batch_id = import_batch_id
    if tags is not None:
        tx.tags = tags
    session.add(tx)
    session.flush()
    return tx


# Import batches
def create_import_batch(
    session: Session,
    *,
    datasource: str | None,
    source_file: str | None,
    summary: str | None = None,
) -> ImportBatch:
    batch = ImportBatch(datasource=datasource, source_file=source_file, summary=summary)
    session.add(batch)
    session.flush()
    return batch


def update_import_batch_summary(session: Session, batch_id: int, summary: str) -> None:
    batch = session.get(ImportBatch, batch_id)
    if not batch:
        return
    batch.summary = summary
    session.add(batch)
    session.flush()


# Dedupe helpers
def find_tx_by_external_id(
    session: Session, *, datasource: str | None, external_id: str
) -> Transaction | None:
    stmt = select(Transaction).where(Transaction.external_id == external_id)
    if datasource is not None:
        stmt = stmt.where(Transaction.datasource == datasource)
    return session.exec(stmt).first()


def find_tx_by_tx_hash(session: Session, *, tx_hash: str) -> Transaction | None:
    stmt = select(Transaction).where(Transaction.tx_hash == tx_hash)
    return session.exec(stmt).first()


# Price helpers
def upsert_price(
    session: Session,
    *,
    asset_symbol: str,
    quote_ccy: str,
    ts: datetime,
    price,
    source: str = "coinmarketcap",
) -> Price:
    # Try find existing unique row
    stmt = select(Price).where(
        (Price.asset_symbol == asset_symbol.upper())
        & (Price.quote_ccy == quote_ccy.upper())
        & (Price.ts == ts)
    )
    existing = session.exec(stmt).first()
    if existing:
        existing.price = price
        existing.source = source
        session.add(existing)
        session.flush()
        return existing
    # ensure asset exists
    ensure_asset(session, asset_symbol)
    row = Price(
        asset_symbol=asset_symbol.upper(),
        quote_ccy=quote_ccy.upper(),
        ts=ts,
        price=price,
        source=source,
    )
    session.add(row)
    session.flush()
    return row


def list_prices(
    session: Session,
    *,
    asset_symbol: str,
    quote_ccy: str = "USD",
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 1000,
    offset: int = 0,
) -> list[Price]:
    stmt = select(Price).where(
        Price.asset_symbol == asset_symbol.upper(), Price.quote_ccy == quote_ccy.upper()
    )
    if since is not None:
        stmt = stmt.where(Price.ts >= since)
    if until is not None:
        stmt = stmt.where(Price.ts <= until)
    stmt = stmt.order_by(Price.ts.desc()).limit(limit).offset(offset)
    return list(session.exec(stmt))


def get_last_price(
    session: Session,
    *,
    asset_symbol: str,
    quote_ccy: str = "USD",
    as_of: datetime | None = None,
) -> Price | None:
    stmt = select(Price).where(
        Price.asset_symbol == asset_symbol.upper(),
        Price.quote_ccy == quote_ccy.upper(),
    )
    if as_of is not None:
        stmt = stmt.where(Price.ts <= as_of)
    stmt = stmt.order_by(Price.ts.desc()).limit(1)
    return session.exec(stmt).first()


# Asset preference helpers
def get_asset_preference(session: Session, symbol: str) -> Optional[str]:
    row = session.get(AssetPreference, symbol.upper())
    return row.preferred_price_source if row else None


def set_asset_preference(
    session: Session, symbol: str, provider: Optional[str]
) -> AssetPreference:
    ensure_asset(session, symbol)
    sym = symbol.upper()
    row = session.get(AssetPreference, sym)
    if row is None:
        row = AssetPreference(asset_symbol=sym, preferred_price_source=provider)
    else:
        row.preferred_price_source = provider
    session.add(row)
    session.flush()
    return row

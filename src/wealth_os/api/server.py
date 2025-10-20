from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wealth_os.core.config import get_config
from wealth_os.db.repo import (
    session_scope,
    list_accounts,
    create_account,
    update_account,
    delete_account,
    list_transactions,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_asset_preference,
    set_asset_preference,
    upsert_price,
)
from wealth_os.db.models import AccountType, TxSide
from wealth_os.core.valuation import summarize_portfolio, compute_holdings
from sqlmodel import select
from sqlalchemy import func
from wealth_os.db import models as dbm
import os

# Ensure providers are registered
import wealth_os.datasources  # noqa: F401
from wealth_os.datasources.registry import get_price_sources
from wealth_os.datasources.base import PriceQuote as DSPriceQuote


app = FastAPI(title="Wealth API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AccountIn(BaseModel):
    name: str
    type: AccountType = AccountType.exchange
    datasource: Optional[str] = None
    external_id: Optional[str] = None
    currency: str = "USD"


class AccountOut(AccountIn):
    id: int
    created_at: datetime


class TxIn(BaseModel):
    ts: Optional[datetime] = None
    account_id: int
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
    import_batch_id: Optional[int] = None
    tags: Optional[str] = None


class TxOut(TxIn):
    id: int


@app.get("/health")
def health():
    return {"status": "ok"}


class QuoteOut(BaseModel):
    symbol: str
    quote_ccy: str = "USD"
    price: Decimal
    ts: datetime
    source: str


def _provider_order(preferred: str | None = None) -> list[str]:
    default = os.getenv("WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk")
    base = [s.strip() for s in default.split(",") if s.strip()]
    out: list[str] = []
    if preferred and preferred not in out:
        out.append(preferred)
    for name in base:
        if name not in out:
            out.append(name)
    return out


def _latest_quote(session, symbol: str, quote: str, first_provider: str | None = None) -> QuoteOut | None:
    sources = get_price_sources()
    # If a provider was explicitly requested, try it first; otherwise use stored preference
    pref = first_provider or get_asset_preference(session, symbol)
    order = _provider_order(pref)
    last_err: Exception | None = None
    sym = symbol.upper()
    qccy = (quote or "USD").upper()
    for name in order:
        if name not in sources:
            continue
        try:
            cls = sources[name]
            src = cls()  # type: ignore[call-arg]
            q: DSPriceQuote = src.get_quote(sym, qccy)
            set_asset_preference(session, sym, src.id())
            # cache the quote as last price for portfolio views
            upsert_price(
                session,
                asset_symbol=sym,
                quote_ccy=q.quote_ccy,
                ts=q.ts,
                price=q.price,
                source=src.id(),
            )
            return QuoteOut(
                symbol=q.symbol, quote_ccy=q.quote_ccy, price=q.price, ts=q.ts, source=src.id()
            )
        except Exception as e:  # pragma: no cover - network errors
            last_err = e
            continue
    return None


@app.get("/accounts", response_model=List[AccountOut])
def api_list_accounts(
    name_like: Optional[str] = None,
    datasource: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        rows = list_accounts(
            s, name_like=name_like, datasource=datasource, limit=limit, offset=offset
        )
        return [AccountOut(**row.dict()) for row in rows]


@app.post("/accounts", response_model=AccountOut)
def api_create_account(body: AccountIn):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        row = create_account(
            s,
            name=body.name,
            type_=body.type,
            datasource=body.datasource,
            external_id=body.external_id,
            currency=body.currency,
        )
        return AccountOut(**row.dict())


@app.put("/accounts/{account_id}", response_model=AccountOut)
def api_update_account(account_id: int, body: AccountIn):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        row = update_account(
            s,
            account_id,
            name=body.name,
            type_=body.type,
            datasource=body.datasource,
            external_id=body.external_id,
            currency=body.currency,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Account not found")
        return AccountOut(**row.dict())


@app.delete("/accounts/{account_id}")
def api_delete_account(account_id: int):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_account(s, account_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Account not found")
    return {"ok": True}


@app.get("/transactions", response_model=List[TxOut])
def api_list_transactions(
    account_id: Optional[int] = None,
    asset_symbol: Optional[str] = Query(None, alias="asset"),
    side: Optional[TxSide] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        rows = list_transactions(
            s,
            account_id=account_id,
            asset_symbol=asset_symbol,
            side=side,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )
        return [TxOut(**row.dict()) for row in rows]


@app.post("/transactions", response_model=TxOut)
def api_create_tx(body: TxIn):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        # Auto-fill price for buy/sell when only qty provided
        eff_price = body.price_quote
        if eff_price is None and body.side in (TxSide.buy, TxSide.sell):
            # If datasource matches a known provider, prefer it for this request
            req_provider = body.datasource if body.datasource in get_price_sources().keys() else None
            q = _latest_quote(s, body.asset_symbol, body.quote_ccy, req_provider)
            if q is not None:
                eff_price = q.price
                # ensure quote ccy aligns
                body.quote_ccy = q.quote_ccy
        row = create_transaction(
            s,
            ts=body.ts or datetime.utcnow(),
            account_id=body.account_id,
            asset_symbol=body.asset_symbol,
            side=body.side,
            qty=body.qty,
            price_quote=eff_price,
            total_quote=body.total_quote,
            quote_ccy=body.quote_ccy,
            fee_qty=body.fee_qty,
            fee_asset=body.fee_asset,
            note=body.note,
            tx_hash=body.tx_hash,
            external_id=body.external_id,
            datasource=body.datasource,
            import_batch_id=body.import_batch_id,
            tags=body.tags,
        )
        return TxOut(**row.dict())


@app.put("/transactions/{tx_id}", response_model=TxOut)
def api_update_tx(tx_id: int, body: TxIn):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        eff_price = body.price_quote
        if eff_price is None and body.side in (TxSide.buy, TxSide.sell):
            req_provider = body.datasource if body.datasource in get_price_sources().keys() else None
            q = _latest_quote(s, body.asset_symbol, body.quote_ccy, req_provider)
            if q is not None:
                eff_price = q.price
                body.quote_ccy = q.quote_ccy
        row = update_transaction(
            s,
            tx_id,
            ts=body.ts,
            account_id=body.account_id,
            asset_symbol=body.asset_symbol,
            side=body.side,
            qty=body.qty,
            price_quote=eff_price,
            total_quote=body.total_quote,
            quote_ccy=body.quote_ccy,
            fee_qty=body.fee_qty,
            fee_asset=body.fee_asset,
            note=body.note,
            tx_hash=body.tx_hash,
            external_id=body.external_id,
            datasource=body.datasource,
            import_batch_id=body.import_batch_id,
            tags=body.tags,
        )
        if not row:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return TxOut(**row.dict())


@app.delete("/transactions/{tx_id}")
def api_delete_tx(tx_id: int):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_transaction(s, tx_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Transaction not found")
    return {"ok": True}


class PositionOut(BaseModel):
    asset: str
    qty: Decimal
    price: Optional[Decimal] = None
    price_ts: Optional[datetime] = None
    value: Optional[Decimal] = None
    cost_open: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Decimal


class TotalsOut(BaseModel):
    value: Decimal
    cost_open: Decimal
    unrealized: Decimal
    realized: Decimal


class PortfolioSummary(BaseModel):
    positions: list[PositionOut]
    totals: TotalsOut


@app.get("/portfolio/summary", response_model=PortfolioSummary)
def api_portfolio_summary(quote: str = "USD", account_id: Optional[int] = None):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        # Best-effort: ensure fresh latest quotes for held assets to make KPIs "live"
        now = datetime.utcnow()
        try:
            holds = compute_holdings(s, as_of=now, account_id=account_id)
            for sym in holds.keys():
                row = get_last_price(s, asset_symbol=sym, quote_ccy=quote)
                # Fetch if missing or older than 5 minutes
                if row is None or (now - row.ts).total_seconds() > 300:
                    _latest_quote(s, sym, quote)
        except Exception:
            # Non-fatal; proceed with whatever cached prices exist
            pass
        positions, totals = summarize_portfolio(
            s, as_of=now, quote=quote, account_id=account_id
        )
        pos = [PositionOut(**p.__dict__) for p in positions]
        tot = TotalsOut(**totals)  # type: ignore[arg-type]
        return PortfolioSummary(positions=pos, totals=tot)


@app.get("/stats")
def api_stats(account_id: Optional[int] = None):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        if account_id is not None:
            accounts_count = s.exec(
                select(func.count(dbm.Account.id)).where(dbm.Account.id == account_id)
            ).one()
            tx_count = s.exec(
                select(func.count(dbm.Transaction.id)).where(
                    dbm.Transaction.account_id == account_id
                )
            ).one()
            return {"accounts": accounts_count, "transactions": tx_count}
        accounts_count = s.exec(select(func.count(dbm.Account.id))).one()
        tx_count = s.exec(select(func.count(dbm.Transaction.id))).one()
    return {"accounts": accounts_count, "transactions": tx_count}


@app.get("/price/quote", response_model=QuoteOut)
def api_price_quote(asset: str, quote: str = "USD", provider: Optional[str] = None):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        req_provider = provider if provider in get_price_sources().keys() else None
        q = _latest_quote(s, asset, quote, req_provider)
        if q is None:
            raise HTTPException(status_code=502, detail="Failed to fetch quote from providers")
        return q


@app.get("/datasource/price", response_model=list[str])
def api_list_price_sources():
    return sorted(get_price_sources().keys())

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
)
from wealth_os.db.models import AccountType, TxSide
from wealth_os.core.valuation import summarize_portfolio
from sqlmodel import select
from sqlalchemy import func
from wealth_os.db import models as dbm


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
        row = create_transaction(
            s,
            ts=body.ts or datetime.utcnow(),
            account_id=body.account_id,
            asset_symbol=body.asset_symbol,
            side=body.side,
            qty=body.qty,
            price_quote=body.price_quote,
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
        row = update_transaction(
            s,
            tx_id,
            ts=body.ts,
            account_id=body.account_id,
            asset_symbol=body.asset_symbol,
            side=body.side,
            qty=body.qty,
            price_quote=body.price_quote,
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
        positions, totals = summarize_portfolio(
            s, as_of=datetime.utcnow(), quote=quote, account_id=account_id
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

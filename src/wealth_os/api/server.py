from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wealth_os.core.config import get_config
from wealth_os.core.context import load_context, save_context
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
    get_last_price,
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
    # Context override > env var
    ctx = load_context()
    default = ctx.providers or os.getenv(
        "WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk"
    )
    base = [s.strip() for s in default.split(",") if s.strip()]
    out: list[str] = []
    if preferred and preferred not in out:
        out.append(preferred)
    for name in base:
        if name not in out:
            out.append(name)
    return out


def _latest_quote(
    session, symbol: str, quote: str, first_provider: str | None = None
) -> QuoteOut | None:
    sources = get_price_sources()
    # If a provider was explicitly requested, try it first; otherwise use stored preference
    pref = first_provider or get_asset_preference(session, symbol)
    order = _provider_order(pref)
    # Try providers in order until one returns a quote
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
                symbol=q.symbol,
                quote_ccy=q.quote_ccy,
                price=q.price,
                ts=q.ts,
                source=src.id(),
            )
        except Exception:  # pragma: no cover - network errors
            continue
    return None


def _ensure_daily_prices(
    session,
    symbol: str,
    quote: str,
    start: datetime,
    end: datetime,
    preferred: str | None = None,
) -> None:
    """Best-effort: fetch and cache daily OHLCV for [start, end] if price table lacks coverage.

    This avoids zero valuations in time-series when only a recent quote exists.
    """
    sources = get_price_sources()
    order = _provider_order(preferred)
    sym = symbol.upper()
    qccy = (quote or "USD").upper()
    # Quick check: do we have any price row within the period?
    from sqlmodel import select
    from wealth_os.db.models import Price

    have = session.exec(
        select(Price)
        .where(
            (Price.asset_symbol == sym)
            & (Price.quote_ccy == qccy)
            & (Price.ts >= start)
            & (Price.ts <= end)
        )
        .limit(1)
    ).first()
    if have:
        return
    for name in order:
        if name not in sources:
            continue
        try:
            cls = sources[name]
            src = cls()  # type: ignore[call-arg]
            points = src.get_ohlcv(sym, start=start, end=end, interval="1d", quote=qccy)
            if not points:
                continue
            for p in points:
                upsert_price(
                    session,
                    asset_symbol=sym,
                    quote_ccy=qccy,
                    ts=p.ts,
                    price=p.close,
                    source=src.id(),
                )
            set_asset_preference(session, sym, src.id())
            return
        except Exception:  # pragma: no cover - network/env errors
            continue
    # If we reach here, we couldn't fetch — silently continue so the series uses what exists


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
            req_provider = (
                body.datasource
                if body.datasource in get_price_sources().keys()
                else None
            )
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
            req_provider = (
                body.datasource
                if body.datasource in get_price_sources().keys()
                else None
            )
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


class RoiPoint(BaseModel):
    date: str  # YYYY-MM-DD
    roi: float  # fraction, e.g., 0.12 for 12%
    value: Optional[float] = None
    cost_open: Optional[float] = None


@app.get("/portfolio/roi_series", response_model=list[RoiPoint])
def api_roi_series(
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    account_id: Optional[int] = None,
    quote: str = "USD",
):
    from datetime import timedelta

    now = datetime.utcnow()
    if until is None:
        until = now
    if since is None:
        since = until - timedelta(days=90)
    # Normalize to dates (strip time)
    start = datetime(since.year, since.month, since.day, 23, 59, 59)
    end = datetime(until.year, until.month, until.day, 23, 59, 59)

    cfg = get_config()
    out: list[RoiPoint] = []
    with session_scope(cfg.db_path) as s:
        cur = start
        while cur <= end:
            positions, totals = summarize_portfolio(
                s, as_of=cur, quote=quote, account_id=account_id
            )
            v = float(totals["value"]) if totals["value"] is not None else 0.0
            c = float(totals["cost_open"]) if totals["cost_open"] is not None else 0.0
            roi = (v - c) / c if c not in (None, 0) else 0.0
            out.append(
                RoiPoint(date=cur.strftime("%Y-%m-%d"), roi=roi, value=v, cost_open=c)
            )
            cur += timedelta(days=1)
    return out


class ValuePoint(BaseModel):
    date: str  # YYYY-MM-DD
    value: float


@app.get("/portfolio/value_series", response_model=list[ValuePoint])
def api_value_series(
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    account_id: Optional[int] = None,
    quote: str = "USD",
):
    from datetime import timedelta

    now = datetime.utcnow()
    if until is None:
        until = now
    if since is None:
        since = until - timedelta(days=90)
    start = datetime(since.year, since.month, since.day, 23, 59, 59)
    end = datetime(until.year, until.month, until.day, 23, 59, 59)

    cfg = get_config()
    out: list[ValuePoint] = []
    with session_scope(cfg.db_path) as s:
        # Attempt to ensure daily prices exist for held assets across the period
        try:
            holds = compute_holdings(s, as_of=end, account_id=account_id)
            for sym in holds.keys():
                pref = get_asset_preference(s, sym)
                _ensure_daily_prices(s, sym, quote, start, end, preferred=pref)
        except Exception:
            pass
        cur = start
        while cur <= end:
            _positions, totals = summarize_portfolio(
                s, as_of=cur, quote=quote, account_id=account_id
            )
            v = float(totals["value"]) if totals["value"] is not None else 0.0
            out.append(ValuePoint(date=cur.strftime("%Y-%m-%d"), value=v))
            cur += timedelta(days=1)
    return out


# Context settings endpoints
class ContextIn(BaseModel):
    account_id: Optional[int] = None
    quote: Optional[str] = None
    providers: Optional[str] = None
    datasource: Optional[str] = None


class ContextOut(ContextIn):
    pass


@app.get("/context", response_model=ContextOut)
def api_get_context():
    ctx = load_context()
    return ContextOut(
        account_id=ctx.account_id,
        quote=ctx.quote,
        providers=ctx.providers,
        datasource=ctx.datasource,
    )


@app.put("/context", response_model=ContextOut)
def api_put_context(body: ContextIn):
    ctx = load_context()
    if body.account_id is not None:
        ctx.account_id = body.account_id
    if body.quote is not None:
        ctx.quote = body.quote
    if body.providers is not None:
        ctx.providers = body.providers
    if body.datasource is not None:
        ctx.datasource = body.datasource
    save_context(ctx)
    return ContextOut(
        account_id=ctx.account_id,
        quote=ctx.quote,
        providers=ctx.providers,
        datasource=ctx.datasource,
    )


# CSV export/import endpoints
@app.get("/export/transactions.csv")
def api_export_transactions_csv(
    account_id: Optional[int] = None,
    asset: Optional[str] = None,
    side: Optional[TxSide] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
):
    import csv
    import io

    cfg = get_config()
    output = io.StringIO()
    w = csv.writer(output)
    # Header aligned with CLI export
    w.writerow(
        [
            "timestamp",
            "account",
            "account_id",
            "asset",
            "side",
            "qty",
            "price_quote",
            "total_quote",
            "quote_ccy",
            "fee_qty",
            "fee_asset",
            "note",
            "tags",
            "tx_hash",
            "external_id",
            "datasource",
            "import_batch_id",
        ]
    )
    with session_scope(cfg.db_path) as s:
        rows = list_transactions(
            s,
            account_id=account_id,
            asset_symbol=asset,
            side=side,
            since=since,
            until=until,
            limit=1000000,
            offset=0,
        )
        # cache account names
        acct_names: dict[int, str] = {}
        from wealth_os.db.repo import get_account

        for t in rows:
            if t.account_id not in acct_names:
                acc = get_account(s, t.account_id)
                acct_names[t.account_id] = acc.name if acc else ""
            w.writerow(
                [
                    t.ts.isoformat(),
                    acct_names.get(t.account_id, ""),
                    t.account_id,
                    t.asset_symbol,
                    t.side,
                    str(t.qty) if t.qty is not None else "",
                    str(t.price_quote) if t.price_quote is not None else "",
                    str(t.total_quote) if t.total_quote is not None else "",
                    t.quote_ccy or "",
                    str(t.fee_qty) if t.fee_qty is not None else "",
                    t.fee_asset or "",
                    t.note or "",
                    t.tags or "",
                    t.tx_hash or "",
                    t.external_id or "",
                    t.datasource or "",
                    t.import_batch_id or "",
                ]
            )
    content = output.getvalue()
    headers = {
        "Content-Type": "text/csv; charset=utf-8",
        "Content-Disposition": "attachment; filename=transactions.csv",
    }
    return Response(content=content, headers=headers, media_type="text/csv")


@app.post("/import/transactions.csv")
def api_import_transactions_csv(
    file: UploadFile = File(...),
    account_id: Optional[int] = Form(None),
    datasource: Optional[str] = Form(None),
    dedupe_by: str = Form("external_id"),
):
    from pathlib import Path
    import tempfile
    from wealth_os.datasources.generic_csv import GenericCSVImportSource
    from wealth_os.db.repo import (
        create_import_batch,
        update_import_batch_summary,
        find_tx_by_external_id,
        find_tx_by_tx_hash,
    )

    if account_id is None:
        raise HTTPException(status_code=400, detail="account_id is required")
    if dedupe_by not in ("external_id", "tx_hash", "none"):
        raise HTTPException(status_code=400, detail="invalid dedupe_by")

    cfg = get_config()
    inserted = 0
    skipped = 0

    # persist upload to a temp file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=Path(file.filename or "").suffix
    ) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        src = GenericCSVImportSource()
        parsed = src.parse_csv(tmp_path, options={"mapping": {}})
        with session_scope(cfg.db_path) as s:
            batch = create_import_batch(
                s,
                datasource=datasource or "generic_csv",
                source_file=str(file.filename),
                summary=None,
            )
            for row in parsed:
                # dedupe
                if dedupe_by == "external_id" and row.external_id:
                    if find_tx_by_external_id(
                        s,
                        datasource=datasource or "generic_csv",
                        external_id=row.external_id,
                    ):
                        skipped += 1
                        continue
                if dedupe_by == "tx_hash" and row.tx_hash:
                    if find_tx_by_tx_hash(s, tx_hash=row.tx_hash):
                        skipped += 1
                        continue
                create_transaction(
                    s,
                    ts=row.ts,
                    account_id=int(account_id),
                    asset_symbol=row.asset_symbol,
                    side=row.side,
                    qty=row.qty,
                    price_quote=row.price_quote,
                    total_quote=row.total_quote,
                    quote_ccy=row.quote_ccy,
                    fee_qty=row.fee_qty,
                    fee_asset=row.fee_asset,
                    note=row.note,
                    tx_hash=row.tx_hash,
                    external_id=row.external_id,
                    datasource=datasource or row.datasource,
                    import_batch_id=batch.id,
                    tags=row.tags,
                )
                inserted += 1
            update_import_batch_summary(
                s,
                batch.id,
                summary=f"Inserted {inserted}, skipped {skipped} (dedupe_by={dedupe_by})",
            )
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass

    return {"inserted": inserted, "skipped": skipped}


@app.get("/price/quote", response_model=QuoteOut)
def api_price_quote(asset: str, quote: str = "USD", provider: Optional[str] = None):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        req_provider = provider if provider in get_price_sources().keys() else None
        q = _latest_quote(s, asset, quote, req_provider)
        if q is None:
            raise HTTPException(
                status_code=502, detail="Failed to fetch quote from providers"
            )
        return q


@app.get("/datasource/price", response_model=list[str])
def api_list_price_sources():
    return sorted(get_price_sources().keys())

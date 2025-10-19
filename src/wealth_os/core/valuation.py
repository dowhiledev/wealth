from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlmodel import Session, select

from wealth_os.db.models import Transaction, TxSide
from wealth_os.db.repo import get_last_price


@dataclass
class Position:
    asset: str
    qty: Decimal
    price: Optional[Decimal]
    price_ts: Optional[datetime]
    value: Optional[Decimal]
    cost_open: Optional[Decimal]
    unrealized_pnl: Optional[Decimal]
    realized_pnl: Decimal


def _dec(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def compute_holdings(
    session: Session, *, as_of: datetime, account_id: int | None = None
) -> Dict[str, Decimal]:
    stmt = select(Transaction).where(Transaction.ts <= as_of)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    stmt = stmt.order_by(Transaction.ts.asc())
    holdings: Dict[str, Decimal] = {}
    rows = session.exec(stmt).all()
    for t in rows:
        sym = t.asset_symbol.upper()
        qty = _dec(t.qty) if t.qty is not None else Decimal(0)
        if t.side in (TxSide.buy, TxSide.transfer_in, TxSide.stake, TxSide.reward):
            holdings[sym] = holdings.get(sym, Decimal(0)) + qty
        elif t.side in (TxSide.sell, TxSide.transfer_out):
            holdings[sym] = holdings.get(sym, Decimal(0)) - qty
        elif t.side == TxSide.fee:
            holdings[sym] = holdings.get(sym, Decimal(0)) - qty
        # apply fee deduction on fee_asset if present
        if t.fee_qty and t.fee_asset:
            fqty = _dec(t.fee_qty)
            fasset = t.fee_asset.upper()
            holdings[fasset] = holdings.get(fasset, Decimal(0)) - fqty
    return {k: v for k, v in holdings.items() if v != 0}


def compute_realized_and_open_cost_fifo(
    session: Session,
    *,
    as_of: datetime,
    account_id: int | None = None,
) -> Tuple[Dict[str, Decimal], Dict[str, Decimal]]:
    """Return (realized_pnl_by_asset, open_cost_basis_by_asset) using FIFO from buy/sell.

    - Only 'buy' lots contribute to cost basis. 'sell' realizes PnL against buy lots.
    - Other sides are ignored for PnL and cost basis.
    - Fees are ignored in PnL to keep it simple for v1.
    """
    stmt = select(Transaction).where(Transaction.ts <= as_of)
    if account_id is not None:
        stmt = stmt.where(Transaction.account_id == account_id)
    stmt = stmt.order_by(Transaction.ts.asc())
    rows = session.exec(stmt).all()

    lots: Dict[
        str, List[Tuple[Decimal, Decimal]]
    ] = {}  # asset -> list of (qty_remaining, cost_per_unit)
    realized: Dict[str, Decimal] = {}
    for t in rows:
        if t.side == TxSide.buy:
            qty = _dec(t.qty)
            if qty == 0:
                continue
            # determine total cost in quote ccy
            total_cost = (
                _dec(t.total_quote)
                if t.total_quote is not None
                else (
                    _dec(t.price_quote) * qty
                    if t.price_quote is not None
                    else Decimal(0)
                )
            )
            cpu = (total_cost / qty) if qty != 0 else Decimal(0)
            lots.setdefault(t.asset_symbol.upper(), []).append([qty, cpu])
        elif t.side == TxSide.sell:
            qty_to_sell = _dec(t.qty)
            proceeds = (
                _dec(t.total_quote)
                if t.total_quote is not None
                else (
                    _dec(t.price_quote) * qty_to_sell
                    if t.price_quote is not None
                    else Decimal(0)
                )
            )
            cost_accum = Decimal(0)
            sym = t.asset_symbol.upper()
            sym_lots = lots.setdefault(sym, [])
            remaining = qty_to_sell
            while remaining > 0 and sym_lots:
                lot_qty, cpu = sym_lots[0]
                take = lot_qty if lot_qty <= remaining else remaining
                cost_accum += take * cpu
                lot_qty = lot_qty - take
                remaining -= take
                if lot_qty == 0:
                    sym_lots.pop(0)
                else:
                    sym_lots[0] = [lot_qty, cpu]
            # If remaining > 0 with no lots, cost is zero (short) for v1
            pnl = proceeds - cost_accum
            realized[sym] = realized.get(sym, Decimal(0)) + pnl
        # ignore other sides for realized pnl

    open_cost: Dict[str, Decimal] = {}
    for sym, sym_lots in lots.items():
        total = Decimal(0)
        for lot_qty, cpu in sym_lots:
            total += lot_qty * cpu
        if total != 0:
            open_cost[sym] = total
    return realized, open_cost


def summarize_portfolio(
    session: Session,
    *,
    as_of: datetime,
    quote: str = "USD",
    account_id: int | None = None,
) -> Tuple[List[Position], Dict[str, Decimal]]:
    holdings = compute_holdings(session, as_of=as_of, account_id=account_id)
    realized_by_asset, open_cost = compute_realized_and_open_cost_fifo(
        session, as_of=as_of, account_id=account_id
    )
    positions: List[Position] = []
    totals = {
        "value": Decimal(0),
        "cost_open": Decimal(0),
        "unrealized": Decimal(0),
        "realized": Decimal(0),
    }
    for sym, qty in sorted(holdings.items()):
        price_row = get_last_price(
            session, asset_symbol=sym, quote_ccy=quote, as_of=as_of
        )
        price = _dec(price_row.price) if price_row is not None else None
        value = (qty * price) if (price is not None) else None
        cost = open_cost.get(sym)
        unreal = (value - cost) if (value is not None and cost is not None) else None
        realized = realized_by_asset.get(sym, Decimal(0))
        positions.append(
            Position(
                asset=sym,
                qty=qty,
                price=price,
                price_ts=price_row.ts if price_row else None,
                value=value,
                cost_open=cost,
                unrealized_pnl=unreal,
                realized_pnl=realized,
            )
        )
        if value is not None:
            totals["value"] += value
        if cost is not None:
            totals["cost_open"] += cost
        if unreal is not None:
            totals["unrealized"] += unreal
        totals["realized"] += realized
    return positions, totals

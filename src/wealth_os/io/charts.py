from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402

from wealth_os.core.valuation import summarize_portfolio
from wealth_os.db.repo import session_scope


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def generate_allocation_pie(
    db_path: str,
    *,
    as_of: datetime,
    quote: str = "USD",
    out: Path,
    account_id: Optional[int] = None,
) -> Path:
    _ensure_parent(out)
    with session_scope(db_path) as s:
        positions, totals = summarize_portfolio(
            s, as_of=as_of, quote=quote, account_id=account_id
        )
    labels: List[str] = []
    values: List[float] = []
    for p in positions:
        if p.value is not None and p.value > 0:
            labels.append(p.asset)
            values.append(float(p.value))
    if not values:
        labels = [p.asset for p in positions]
        values = [float(p.qty) for p in positions]

    plt.figure(figsize=(6, 6))
    sns.set_style("whitegrid")
    plt.pie(values, labels=labels, autopct="%1.1f%%", startangle=140)
    plt.title(f"Allocation as of {as_of.date()} ({quote})")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def _daterange(start: date, end: date) -> Iterable[date]:
    d = start
    while d <= end:
        yield d
        d = d + timedelta(days=1)


def generate_value_timeseries_line(
    db_path: str,
    *,
    since: datetime,
    until: datetime,
    quote: str = "USD",
    out: Path,
    account_id: Optional[int] = None,
) -> Path:
    _ensure_parent(out)
    xs: List[datetime] = []
    ys: List[float] = []
    with session_scope(db_path) as s:
        for d in _daterange(since.date(), until.date()):
            as_of = datetime(d.year, d.month, d.day, 23, 59, 59)
            positions, totals = summarize_portfolio(
                s, as_of=as_of, quote=quote, account_id=account_id
            )
            xs.append(as_of)
            ys.append(float(totals["value"]))

    plt.figure(figsize=(9, 4))
    sns.set_style("whitegrid")
    plt.plot(xs, ys, marker="o", linewidth=1.5)
    plt.title(f"Portfolio Value ({quote})")
    plt.xlabel("Date")
    plt.ylabel(f"Value ({quote})")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    return out


def generate_realized_pnl_bar(
    db_path: str,
    *,
    since: datetime,
    until: datetime,
    quote: str = "USD",
    out: Path,
    account_id: Optional[int] = None,
) -> Path:
    """Compute FIFO realized PnL as we scan transactions and aggregate by month of the sell date."""
    _ensure_parent(out)
    from sqlmodel import select
    from wealth_os.db.models import Transaction, TxSide

    def ym(dt: datetime) -> str:
        return dt.strftime("%Y-%m")

    monthly: Dict[str, Decimal] = defaultdict(Decimal)
    # FIFO lots per asset
    lots: Dict[str, List[Tuple[Decimal, Decimal]]] = {}
    with session_scope(db_path) as s:
        stmt = select(Transaction).where(
            Transaction.ts >= since, Transaction.ts <= until
        )
        if account_id is not None:
            stmt = stmt.where(Transaction.account_id == account_id)
        stmt = stmt.order_by(Transaction.ts.asc())
        rows = s.exec(stmt).all()
        for t in rows:
            if t.side == TxSide.buy:
                qty = Decimal(str(t.qty))
                if qty == 0:
                    continue
                total = (
                    Decimal(str(t.total_quote))
                    if t.total_quote is not None
                    else (
                        Decimal(str(t.price_quote)) * qty
                        if t.price_quote is not None
                        else Decimal(0)
                    )
                )
                cpu = (total / qty) if qty != 0 else Decimal(0)
                lots.setdefault(t.asset_symbol.upper(), []).append([qty, cpu])
            elif t.side == TxSide.sell:
                qty_to_sell = Decimal(str(t.qty))
                proceeds = (
                    Decimal(str(t.total_quote))
                    if t.total_quote is not None
                    else (
                        Decimal(str(t.price_quote)) * qty_to_sell
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
                pnl = proceeds - cost_accum
                monthly[ym(t.ts)] += pnl

    xs = sorted(monthly.keys())
    ys = [float(monthly[m]) for m in xs]
    plt.figure(figsize=(9, 4))
    sns.set_style("whitegrid")
    plt.bar(xs, ys)
    plt.title("Realized PnL by Month")
    plt.xlabel("Month")
    plt.ylabel(f"PnL ({quote})")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    return out

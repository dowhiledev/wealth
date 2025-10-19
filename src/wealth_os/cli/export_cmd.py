from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from wealth_os.core.config import get_config
from wealth_os.db.models import TxSide
from wealth_os.db.repo import session_scope, list_transactions, get_account


app = typer.Typer(help="Export data")


HEADER = [
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


@app.command("csv")
def export_csv(
    out: Path = typer.Option(..., "--out", help="Output CSV file path"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
    asset: Optional[str] = typer.Option(None, "--asset"),
    side: Optional[TxSide] = typer.Option(None, "--side", case_sensitive=False),
    since: Optional[datetime] = typer.Option(None, "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
) -> None:
    cfg = get_config()
    out.parent.mkdir(parents=True, exist_ok=True)

    with session_scope(cfg.db_path) as s:
        offset = 0
        limit = 1000
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(HEADER)
            while True:
                rows = list_transactions(
                    s,
                    account_id=account_id,
                    asset_symbol=asset,
                    side=side,
                    since=since,
                    until=until,
                    limit=limit,
                    offset=offset,
                )
                if not rows:
                    break
                # cache account names
                acct_names = {}
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
                offset += len(rows)
    typer.echo(f"Exported transactions to {out}")

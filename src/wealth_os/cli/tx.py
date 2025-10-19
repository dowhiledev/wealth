from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import typer
from wealth_os.cli.ui import console, fmt_decimal, success_panel

from wealth_os.core.config import get_config
from wealth_os.core.context import load_context
from wealth_os.db.models import TxSide
from wealth_os.db.repo import (
    session_scope,
    create_transaction,
    delete_transaction,
    list_transactions,
    update_transaction,
)


app = typer.Typer(help="Manage transactions")


@app.command("add")
def add(
    account_id: Optional[int] = typer.Option(
        None, "--account-id", help="Defaults to context account_id if not provided"
    ),
    asset: str = typer.Option(..., "--asset", help="Asset symbol, e.g., BTC"),
    side: TxSide = typer.Option(..., "--side", case_sensitive=False),
    qty: str = typer.Option(..., "--qty"),
    ts: Optional[datetime] = typer.Option(
        None, "--ts", help="Timestamp (ISO); defaults to now"
    ),
    price_quote: Optional[str] = typer.Option(None, "--price-quote"),
    total_quote: Optional[str] = typer.Option(None, "--total-quote"),
    quote_ccy: str = typer.Option("USD", "--quote-ccy"),
    fee_qty: Optional[str] = typer.Option(None, "--fee-qty"),
    fee_asset: Optional[str] = typer.Option(None, "--fee-asset"),
    note: Optional[str] = typer.Option(None, "--note"),
    tx_hash: Optional[str] = typer.Option(None, "--tx-hash"),
    external_id: Optional[str] = typer.Option(None, "--external-id"),
    datasource: Optional[str] = typer.Option(None, "--datasource"),
    import_batch_id: Optional[int] = typer.Option(None, "--import-batch-id"),
    tags: Optional[str] = typer.Option(None, "--tags"),
):
    cfg = get_config()
    ctx = load_context()

    # Convert decimals from strings
    def _to_dec(x: Optional[str]) -> Optional[Decimal]:
        if x is None:
            return None
        try:
            return Decimal(str(x))
        except InvalidOperation:
            raise typer.BadParameter(f"Invalid decimal value: {x}")

    with session_scope(cfg.db_path) as s:
        tx = create_transaction(
            s,
            ts=ts or datetime.utcnow(),
            account_id=account_id or ctx.account_id or -1,
            asset_symbol=asset,
            side=side,
            qty=_to_dec(qty),
            price_quote=_to_dec(price_quote),
            total_quote=_to_dec(total_quote),
            quote_ccy=quote_ccy,
            fee_qty=_to_dec(fee_qty),
            fee_asset=fee_asset,
            note=note,
            tx_hash=tx_hash,
            external_id=external_id,
            datasource=datasource,
            import_batch_id=import_batch_id,
            tags=tags,
        )
        if (account_id or ctx.account_id) is None:
            raise typer.BadParameter(
                "--account-id is required (set via --account-id or `wealth context set account_id <id>`)"
            )
        console.print(
            success_panel(
                f"Created tx id={tx.id} asset={tx.asset_symbol} side={tx.side} qty={fmt_decimal(tx.qty)}"
            )
        )


@app.command("list")
def list_(
    account_id: Optional[int] = typer.Option(
        None, "--account-id", help="Defaults to context account_id if not provided"
    ),
    asset: Optional[str] = typer.Option(None, "--asset"),
    side: Optional[TxSide] = typer.Option(None, "--side", case_sensitive=False),
    since: Optional[datetime] = typer.Option(None, "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
    limit: int = typer.Option(100, "--limit"),
    offset: int = typer.Option(0, "--offset"),
):
    cfg = get_config()
    ctx = load_context()
    from rich.table import Table

    with session_scope(cfg.db_path) as s:
        rows = list_transactions(
            s,
            account_id=account_id or ctx.account_id,
            asset_symbol=asset,
            side=side,
            since=since,
            until=until,
            limit=limit,
            offset=offset,
        )
        if not rows:
            console.print("[yellow]No transactions found.[/yellow]")
            raise typer.Exit(code=0)
        table = Table(title="Transactions")
        table.add_column("ID", justify="right")
        table.add_column("Timestamp")
        table.add_column("Acct", justify="right")
        table.add_column("Asset")
        table.add_column("Side")
        table.add_column("Qty", justify="right")
        table.add_column("Price", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("QCCY")
        for t in rows:
            side_str = str(t.side)
            side_style = (
                "green"
                if "buy" in side_str
                else ("red" if "sell" in side_str else "yellow")
            )
            table.add_row(
                str(t.id),
                t.ts.isoformat(),
                str(t.account_id),
                t.asset_symbol,
                f"[{side_style}]{t.side}[/{side_style}]",
                fmt_decimal(t.qty),
                fmt_decimal(t.price_quote),
                fmt_decimal(t.total_quote),
                t.quote_ccy or "",
            )
        console.print(table)


@app.command("edit")
def edit(
    id: int = typer.Option(..., "--id"),
    ts: Optional[datetime] = typer.Option(None, "--ts"),
    account_id: Optional[int] = typer.Option(
        None, "--account-id", help="Defaults to context account_id if not provided"
    ),
    asset: Optional[str] = typer.Option(None, "--asset"),
    side: Optional[TxSide] = typer.Option(None, "--side", case_sensitive=False),
    qty: Optional[str] = typer.Option(None, "--qty"),
    price_quote: Optional[str] = typer.Option(None, "--price-quote"),
    total_quote: Optional[str] = typer.Option(None, "--total-quote"),
    quote_ccy: Optional[str] = typer.Option(None, "--quote-ccy"),
    fee_qty: Optional[str] = typer.Option(None, "--fee-qty"),
    fee_asset: Optional[str] = typer.Option(None, "--fee-asset"),
    note: Optional[str] = typer.Option(None, "--note"),
    tx_hash: Optional[str] = typer.Option(None, "--tx-hash"),
    external_id: Optional[str] = typer.Option(None, "--external-id"),
    datasource: Optional[str] = typer.Option(None, "--datasource"),
    import_batch_id: Optional[int] = typer.Option(None, "--import-batch-id"),
    tags: Optional[str] = typer.Option(None, "--tags"),
):
    cfg = get_config()
    ctx = load_context()

    def _to_dec(x: Optional[str]) -> Optional[Decimal]:
        if x is None:
            return None
        try:
            return Decimal(str(x))
        except InvalidOperation:
            raise typer.BadParameter(f"Invalid decimal value: {x}")

    with session_scope(cfg.db_path) as s:
        tx = update_transaction(
            s,
            id,
            ts=ts,
            account_id=account_id or ctx.account_id,
            asset_symbol=asset,
            side=side,
            qty=_to_dec(qty),
            price_quote=_to_dec(price_quote),
            total_quote=_to_dec(total_quote),
            quote_ccy=quote_ccy,
            fee_qty=_to_dec(fee_qty),
            fee_asset=fee_asset,
            note=note,
            tx_hash=tx_hash,
            external_id=external_id,
            datasource=datasource,
            import_batch_id=import_batch_id,
            tags=tags,
        )
        if tx:
            console.print(success_panel(f"Updated tx id={tx.id}"))
    if not tx:
        console.print("[red]Transaction not found.[/red]")
        raise typer.Exit(code=1)


@app.command("rm")
def rm(id: int = typer.Option(..., "--id")):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_transaction(s, id)
    if not ok:
        console.print("[red]Transaction not found.[/red]")
        raise typer.Exit(code=1)
    console.print(success_panel("Deleted transaction."))

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import typer

from wealth.core.config import get_config
from wealth.db.models import TxSide
from wealth.db.repo import (
    session_scope,
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    update_transaction,
)


app = typer.Typer(help="Manage transactions")


@app.command("add")
def add(
    account_id: int = typer.Option(..., "--account-id"),
    asset: str = typer.Option(..., "--asset", help="Asset symbol, e.g., BTC"),
    side: TxSide = typer.Option(..., "--side", case_sensitive=False),
    qty: str = typer.Option(..., "--qty"),
    ts: Optional[datetime] = typer.Option(None, "--ts", help="Timestamp (ISO); defaults to now"),
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
            account_id=account_id,
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
        typer.echo(f"Created tx id={tx.id} asset={tx.asset_symbol} side={tx.side} qty={tx.qty}")


@app.command("list")
def list_(
    account_id: Optional[int] = typer.Option(None, "--account-id"),
    asset: Optional[str] = typer.Option(None, "--asset"),
    side: Optional[TxSide] = typer.Option(None, "--side", case_sensitive=False),
    since: Optional[datetime] = typer.Option(None, "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
    limit: int = typer.Option(100, "--limit"),
    offset: int = typer.Option(0, "--offset"),
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
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
            typer.echo("No transactions found.")
            raise typer.Exit(code=0)
        typer.echo("id   ts                        acct  asset  side          qty        price_quote  total_quote  qccy")
        for t in rows:
            typer.echo(
                f"{t.id:<4} {t.ts.isoformat():<24} {t.account_id:<5} {t.asset_symbol:<5} {t.side:<12} {t.qty:<10} {str(t.price_quote or ''):<12} {str(t.total_quote or ''):<12} {t.quote_ccy or ''}"
            )


@app.command("edit")
def edit(
    id: int = typer.Option(..., "--id"),
    ts: Optional[datetime] = typer.Option(None, "--ts"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
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
            account_id=account_id,
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
            typer.echo(f"Updated tx id={tx.id}")
    if not tx:
        typer.echo("Transaction not found.")
        raise typer.Exit(code=1)


@app.command("rm")
def rm(id: int = typer.Option(..., "--id")):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_transaction(s, id)
    if not ok:
        typer.echo("Transaction not found.")
        raise typer.Exit(code=1)
    typer.echo("Deleted transaction.")

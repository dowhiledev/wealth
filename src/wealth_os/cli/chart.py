from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from wealth_os.core.config import get_config
from wealth_os.io.charts import (
    generate_allocation_pie,
    generate_realized_pnl_bar,
    generate_value_timeseries_line,
)


app = typer.Typer(help="Generate charts")


@app.command("allocation")
def chart_allocation(
    out: Path = typer.Option(..., "--out", help="Output PNG path"),
    as_of: Optional[datetime] = typer.Option(None, "--as-of", help="As-of time"),
    quote: str = typer.Option("USD", "--quote"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
) -> None:
    cfg = get_config()
    as_of = as_of or datetime.utcnow()
    generate_allocation_pie(
        cfg.db_path, as_of=as_of, quote=quote, out=out, account_id=account_id
    )
    typer.echo(f"Saved allocation chart to {out}")


@app.command("value")
def chart_value(
    out: Path = typer.Option(..., "--out", help="Output PNG path"),
    since: datetime = typer.Option(..., "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
    quote: str = typer.Option("USD", "--quote"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
) -> None:
    cfg = get_config()
    until = until or datetime.utcnow()
    generate_value_timeseries_line(
        cfg.db_path,
        since=since,
        until=until,
        quote=quote,
        out=out,
        account_id=account_id,
    )
    typer.echo(f"Saved value chart to {out}")


@app.command("pnl")
def chart_pnl(
    out: Path = typer.Option(..., "--out", help="Output PNG path"),
    since: datetime = typer.Option(..., "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
    quote: str = typer.Option("USD", "--quote"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
) -> None:
    cfg = get_config()
    until = until or datetime.utcnow()
    generate_realized_pnl_bar(
        cfg.db_path,
        since=since,
        until=until,
        quote=quote,
        out=out,
        account_id=account_id,
    )
    typer.echo(f"Saved PnL chart to {out}")

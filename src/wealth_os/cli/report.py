from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer

from wealth_os.core.config import get_config
from wealth_os.io.charts import (
    generate_allocation_pie,
    generate_realized_pnl_bar,
    generate_value_timeseries_line,
)
from wealth_os.io.pdf_report import generate_pdf_report


app = typer.Typer(help="Generate PDF report")


@app.command("generate")
def generate(
    out: Path = typer.Option(..., "--out", help="Output PDF path"),
    as_of: Optional[datetime] = typer.Option(None, "--as-of"),
    since: Optional[datetime] = typer.Option(None, "--since"),
    until: Optional[datetime] = typer.Option(None, "--until"),
    quote: str = typer.Option("USD", "--quote"),
    account_id: Optional[int] = typer.Option(None, "--account-id"),
    include_allocation: bool = typer.Option(
        True, "--include-allocation/--no-allocation"
    ),
    include_value: bool = typer.Option(True, "--include-value/--no-value"),
    include_pnl: bool = typer.Option(True, "--include-pnl/--no-pnl"),
) -> None:
    cfg = get_config()
    as_of = as_of or datetime.utcnow()
    until = until or as_of
    since = since or (until - timedelta(days=30))

    charts_dir = Path("reports")
    charts_dir.mkdir(parents=True, exist_ok=True)
    allocation_img = None
    value_img = None
    pnl_img = None

    if include_allocation:
        allocation_img = charts_dir / f"allocation_{as_of.date()}.png"
        generate_allocation_pie(
            cfg.db_path,
            as_of=as_of,
            quote=quote,
            out=allocation_img,
            account_id=account_id,
        )
    if include_value:
        value_img = charts_dir / f"value_{since.date()}_{until.date()}.png"
        generate_value_timeseries_line(
            cfg.db_path,
            since=since,
            until=until,
            quote=quote,
            out=value_img,
            account_id=account_id,
        )
    if include_pnl:
        pnl_img = charts_dir / f"pnl_{since.date()}_{until.date()}.png"
        generate_realized_pnl_bar(
            cfg.db_path,
            since=since,
            until=until,
            quote=quote,
            out=pnl_img,
            account_id=account_id,
        )

    generate_pdf_report(
        cfg.db_path,
        out_pdf=out,
        as_of=as_of,
        quote=quote,
        account_id=account_id,
        allocation_img=allocation_img,
        value_img=value_img,
        pnl_img=pnl_img,
    )
    typer.echo(f"Generated report at {out}")

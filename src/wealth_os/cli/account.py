from __future__ import annotations

from typing import Optional

import typer
from wealth_os.cli.ui import console, success_panel

from wealth_os.core.config import get_config
from wealth_os.db.repo import (
    session_scope,
    create_account,
    delete_account,
    list_accounts,
    update_account,
)
from wealth_os.db.models import AccountType


app = typer.Typer(help="Manage accounts")


@app.command("add")
def add(
    name: str = typer.Option(..., "--name", help="Account name"),
    type: AccountType = typer.Option(
        AccountType.exchange, "--type", case_sensitive=False, help="Account type"
    ),
    datasource: Optional[str] = typer.Option(
        None, "--datasource", help="Datasource label"
    ),
    external_id: Optional[str] = typer.Option(
        None, "--external-id", help="External/account ID at provider"
    ),
    currency: str = typer.Option(
        "USD", "--currency", help="Primary currency for the account"
    ),
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        acc = create_account(
            s,
            name=name,
            type_=type,
            datasource=datasource,
            external_id=external_id,
            currency=currency,
        )
        console.print(
            success_panel(
                f"Created account id={acc.id} name={acc.name} type={acc.type}"
            )
        )


@app.command("list")
def list_(
    name_like: Optional[str] = typer.Option(None, "--name-like"),
    datasource: Optional[str] = typer.Option(None, "--datasource"),
    limit: int = typer.Option(100, "--limit"),
    offset: int = typer.Option(0, "--offset"),
):
    cfg = get_config()
    from rich.table import Table

    with session_scope(cfg.db_path) as s:
        rows = list_accounts(
            s, name_like=name_like, datasource=datasource, limit=limit, offset=offset
        )
        if not rows:
            console.print("[yellow]No accounts found.[/yellow]")
            raise typer.Exit(code=0)
        table = Table(title="Accounts", show_lines=False)
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Currency")
        table.add_column("Datasource")
        table.add_column("Created")
        for a in rows:
            table.add_row(
                str(a.id),
                a.name,
                str(a.type),
                a.currency,
                a.datasource or "-",
                a.created_at.isoformat(),
            )
        console.print(table)


@app.command("edit")
def edit(
    id: int = typer.Option(..., "--id", help="Account id"),
    name: Optional[str] = typer.Option(None, "--name"),
    type: Optional[AccountType] = typer.Option(None, "--type", case_sensitive=False),
    datasource: Optional[str] = typer.Option(None, "--datasource"),
    external_id: Optional[str] = typer.Option(None, "--external-id"),
    currency: Optional[str] = typer.Option(None, "--currency"),
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        acc = update_account(
            s,
            id,
            name=name,
            type_=type,
            datasource=datasource,
            external_id=external_id,
            currency=currency,
        )
        if acc:
            console.print(
                success_panel(
                    f"Updated account id={acc.id} name={acc.name} type={acc.type}"
                )
            )
    if not acc:
        console.print("[red]Account not found.[/red]")
        raise typer.Exit(code=1)


@app.command("rm")
def rm(id: int = typer.Option(..., "--id", help="Account id")):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_account(s, id)
    if not ok:
        console.print("[red]Account not found.[/red]")
        raise typer.Exit(code=1)
    console.print(success_panel("Deleted account."))

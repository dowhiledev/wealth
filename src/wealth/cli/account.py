from __future__ import annotations

from typing import Optional

import typer

from wealth.core.config import get_config
from wealth.db.repo import (
    session_scope,
    create_account,
    delete_account,
    list_accounts,
    update_account,
)
from wealth.db.models import AccountType


app = typer.Typer(help="Manage accounts")


@app.command("add")
def add(
    name: str = typer.Option(..., "--name", help="Account name"),
    type: AccountType = typer.Option(AccountType.exchange, "--type", case_sensitive=False, help="Account type"),
    datasource: Optional[str] = typer.Option(None, "--datasource", help="Datasource label"),
    external_id: Optional[str] = typer.Option(None, "--external-id", help="External/account ID at provider"),
    currency: str = typer.Option("USD", "--currency", help="Primary currency for the account"),
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        acc = create_account(s, name=name, type_=type, datasource=datasource, external_id=external_id, currency=currency)
        typer.echo(f"Created account id={acc.id} name={acc.name} type={acc.type}")


@app.command("list")
def list_(
    name_like: Optional[str] = typer.Option(None, "--name-like"),
    datasource: Optional[str] = typer.Option(None, "--datasource"),
    limit: int = typer.Option(100, "--limit"),
    offset: int = typer.Option(0, "--offset"),
):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        rows = list_accounts(s, name_like=name_like, datasource=datasource, limit=limit, offset=offset)
        if not rows:
            typer.echo("No accounts found.")
            raise typer.Exit(code=0)
        typer.echo("id  name                  type       currency  datasource")
        for a in rows:
            typer.echo(f"{a.id:<3} {a.name:<20} {a.type:<10} {a.currency:<8} {a.datasource or '-'}")


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
        acc = update_account(s, id, name=name, type_=type, datasource=datasource, external_id=external_id, currency=currency)
        if acc:
            typer.echo(f"Updated account id={acc.id} name={acc.name} type={acc.type}")
    if not acc:
        typer.echo("Account not found.")
        raise typer.Exit(code=1)


@app.command("rm")
def rm(id: int = typer.Option(..., "--id", help="Account id")):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        ok = delete_account(s, id)
    if not ok:
        typer.echo("Account not found.")
        raise typer.Exit(code=1)
    typer.echo("Deleted account.")

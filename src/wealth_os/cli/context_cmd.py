from __future__ import annotations


import typer
from rich.table import Table

from wealth_os.cli.ui import console, success_panel, info_panel
from wealth_os.core.context import (
    load_context,
    set_value,
    unset_value,
    get_context_path,
)


app = typer.Typer(help="Manage CLI context defaults")


@app.command("show")
def show() -> None:
    ctx = load_context()
    table = Table(title="Wealth Context")
    table.add_column("Key")
    table.add_column("Value")
    table.add_row(
        "account_id", str(ctx.account_id) if ctx.account_id is not None else "-"
    )
    table.add_row("quote", ctx.quote or "-")
    table.add_row("providers", ctx.providers or "-")
    table.add_row("datasource", ctx.datasource or "-")
    console.print(table)
    console.print(info_panel(f"Context file: {get_context_path()}"))


@app.command("get")
def get(key: str) -> None:
    ctx = load_context()
    if not hasattr(ctx, key):
        console.print(f"[red]Unknown context key: {key}[/red]")
        raise typer.Exit(code=1)
    console.print(str(getattr(ctx, key)))


@app.command("set")
def set_(
    key: str = typer.Argument(..., help="Key: account_id|quote|providers|datasource"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    if key == "account_id":
        try:
            intval = int(value)
        except ValueError:
            console.print("[red]account_id must be an integer[/red]")
            raise typer.Exit(code=1)
        set_value("account_id", intval)
    else:
        set_value(key, value)
    console.print(success_panel(f"Set {key}={value}"))


@app.command("unset")
def unset(key: str) -> None:
    try:
        unset_value(key)
    except KeyError:
        console.print(f"[red]Unknown context key: {key}[/red]")
        raise typer.Exit(code=1)
    console.print(success_panel(f"Unset {key}"))

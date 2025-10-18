from __future__ import annotations

import logging
from typing import Optional

import typer

from .core.config import get_config
from .db.engine import init_db


app = typer.Typer(help="Wealth CLI — manage crypto transactions and reports.")


def _setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


@app.callback()
def _app_callback(
    ctx: typer.Context,
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity (-v, -vv)"),
) -> None:
    """Global options and initialization."""
    _setup_logging(verbose)


@app.command()
def init() -> None:
    """Initialize the local SQLite database using current configuration."""
    cfg = get_config()
    init_db(cfg.db_path)
    typer.echo(f"Initialized database at: {cfg.db_path}")


config_app = typer.Typer(help="Configuration commands")


@config_app.command("show")
def config_show() -> None:
    """Show current configuration as seen by the CLI."""
    cfg = get_config()
    api_present = bool(cfg.coinmarketcap_api_key)
    lines = [
        f"db_path: {cfg.db_path}",
        f"base_currency: {cfg.base_currency}",
        f"coinmarketcap_api_key_set: {api_present}",
    ]
    typer.echo("\n".join(lines))


app.add_typer(config_app, name="config")


def main() -> None:
    app()

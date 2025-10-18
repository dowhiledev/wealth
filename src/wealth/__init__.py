from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime
import time

import typer

from .core.config import get_config
from .db.engine import init_db
from .db.repo import session_scope, upsert_price, list_prices


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
    lines = [
        f"db_path: {cfg.db_path}",
        f"base_currency: {cfg.base_currency}",
    ]
    typer.echo("\n".join(lines))


app.add_typer(config_app, name="config")


datasource_app = typer.Typer(help="Datasource commands")


@datasource_app.command("list")
def datasource_list() -> None:
    """List available price and import datasources."""
    # Ensure providers are imported and registered
    import wealth.datasources  # noqa: F401
    from wealth.datasources.registry import get_import_sources, get_price_sources

    price_sources = get_price_sources()
    import_sources = get_import_sources()

    typer.echo("Price sources:")
    if price_sources:
        for key in sorted(price_sources.keys()):
            typer.echo(f"  - {key}")
    else:
        typer.echo("  (none)")

    typer.echo("Import sources:")
    if import_sources:
        for key in sorted(import_sources.keys()):
            typer.echo(f"  - {key}")
    else:
        typer.echo("  (none)")


app.add_typer(datasource_app, name="datasource")


price_app = typer.Typer(help="Price data commands")


@price_app.command("sync")
def price_sync(
    assets: str = typer.Option(..., "--assets", help="Comma-separated symbols, e.g., BTC,ETH"),
    since: datetime = typer.Option(..., "--since", help="Start date/time (YYYY-MM-DD or ISO)"),
    until: Optional[datetime] = typer.Option(None, "--until", help="End date/time; defaults to now"),
    quote: str = typer.Option("USD", "--quote", help="Quote currency (e.g., USD)"),
    interval: str = typer.Option("1d", "--interval", help="Interval: 1d|daily"),
) -> None:
    """Fetch historical prices from CoinMarketCap and store in DB."""
    # Ensure providers are registered
    import wealth.datasources  # noqa: F401
    from wealth.datasources.coinmarketcap import CoinMarketCapPriceSource

    cfg = get_config()
    until = until or datetime.utcnow()
    # Allow sandbox override via CLI
    src = CoinMarketCapPriceSource()
    symbols = [s.strip().upper() for s in assets.split(",") if s.strip()]

    total = 0
    try:
        for sym in symbols:
            typer.echo(f"Syncing {sym} {quote} {interval} from {since.date()} to {until.date()}...")
            points = src.get_ohlcv(sym, start=since, end=until, interval=interval, quote=quote)
            with session_scope(cfg.db_path) as s:
                for p in points:
                    upsert_price(s, asset_symbol=sym, quote_ccy=quote, ts=p.ts, price=p.close, source=src.id())
            total += len(points)
            time.sleep(0.25)  # be gentle with rate limits
    except Exception as e:
        typer.echo(f"Error during price sync: {e}")
        raise typer.Exit(code=1)
    typer.echo(f"Inserted/updated {total} price points across {len(symbols)} assets.")


@price_app.command("quote")
def price_quote(
    asset: str = typer.Option(..., "--asset", help="Asset symbol, e.g., BTC"),
    quote: str = typer.Option("USD", "--quote", help="Quote currency"),
) -> None:
    """Fetch and display the latest quote from CoinMarketCap."""
    import wealth.datasources  # noqa
    from wealth.datasources.coinmarketcap import CoinMarketCapPriceSource
    base_url_override = None
    src = CoinMarketCapPriceSource()
    q = src.get_quote(asset, quote)
    typer.echo(f"{q.symbol}/{q.quote_ccy} price={q.price} ts={q.ts.isoformat()}")


@price_app.command("show")
def price_show(
    asset: str = typer.Option(..., "--asset", help="Asset symbol, e.g., BTC"),
    since: Optional[datetime] = typer.Option(None, "--since", help="Start date/time (ISO)"),
    quote: str = typer.Option("USD", "--quote", help="Quote currency"),
    limit: int = typer.Option(20, "--limit", help="Limit number of rows"),
) -> None:
    """Show cached prices from the local DB."""
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        rows = list_prices(s, asset_symbol=asset, quote_ccy=quote, since=since, limit=limit)
    if not rows:
        typer.echo("No prices found.")
        raise typer.Exit(code=0)
    for r in rows:
        typer.echo(f"{r.asset_symbol}/{r.quote_ccy} {r.ts.isoformat()} close={r.price}")


app.add_typer(price_app, name="price")

# Domain subcommands
from .cli.account import app as account_app
from .cli.tx import app as tx_app
from .cli.import_cmd import app as import_app
from .cli.export_cmd import app as export_app

app.add_typer(account_app, name="account")
app.add_typer(tx_app, name="tx")
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")


def main() -> None:
    app()

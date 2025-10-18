from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime
import time
import os

import typer

from .core.config import get_config
from .db.engine import init_db
from .db.repo import session_scope, upsert_price, list_prices, get_asset_preference, set_asset_preference
from .core.valuation import summarize_portfolio


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
    # Ensure .env is loaded early for all commands
    cfg = get_config()
    # Ensure DB exists and new tables are created (simple create_all)
    try:
        init_db(cfg.db_path)
    except Exception:
        # Best-effort; commands can also initialize explicitly
        pass


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
    providers: Optional[str] = typer.Option(None, "--providers", help="Comma-separated provider order, e.g., coindesk,coinmarketcap"),
) -> None:
    """Fetch historical prices from CoinMarketCap and store in DB."""
    # Ensure providers are registered
    import wealth.datasources  # noqa: F401
    from wealth.datasources.registry import get_price_sources

    cfg = get_config()
    until = until or datetime.utcnow()
    all_sources = get_price_sources()
    default_order = [s.strip() for s in os.getenv("WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk").split(",") if s.strip()]
    cli_order = [s.strip() for s in providers.split(",")] if providers else None
    base_order = cli_order or default_order
    symbols = [s.strip().upper() for s in assets.split(",") if s.strip()]

    total = 0
    try:
        for sym in symbols:
            # Build order using per-asset preference then base order
            with session_scope(cfg.db_path) as s:
                preferred = get_asset_preference(s, sym)
            order = []
            if preferred:
                order.append(preferred)
            for name in base_order:
                if name not in order:
                    order.append(name)

            last_err = None
            success = False
            for prov_name in order:
                if prov_name not in all_sources:
                    continue
                try:
                    src_cls = all_sources[prov_name]
                    src = src_cls()  # type: ignore[call-arg]
                except Exception as e:
                    last_err = e
                    continue
                typer.echo(f"Syncing {sym} via {prov_name} {quote} {interval} from {since.date()} to {until.date()}...")
                try:
                    points = src.get_ohlcv(sym, start=since, end=until, interval=interval, quote=quote)
                except Exception as e:
                    last_err = e
                    typer.echo(f"  Provider {prov_name} failed: {e}")
                    continue
                if not points:
                    typer.echo(f"  Provider {prov_name} returned no data; trying next")
                    continue
                with session_scope(cfg.db_path) as s:
                    for p in points:
                        upsert_price(s, asset_symbol=sym, quote_ccy=quote, ts=p.ts, price=p.close, source=src.id())
                    set_asset_preference(s, sym, src.id())
                total += len(points)
                success = True
                break
            if not success:
                msg = f"Failed to sync {sym} from all providers"
                if last_err:
                    msg += f": last error: {last_err}"
                raise RuntimeError(msg)
            time.sleep(0.25)  # be gentle with rate limits
    except Exception as e:
        typer.echo(f"Error during price sync: {e}")
        raise typer.Exit(code=1)
    typer.echo(f"Inserted/updated {total} price points across {len(symbols)} assets.")


@price_app.command("quote")
def price_quote(
    asset: str = typer.Option(..., "--asset", help="Asset symbol, e.g., BTC"),
    quote: str = typer.Option("USD", "--quote", help="Quote currency"),
    providers: Optional[str] = typer.Option(None, "--providers", help="Comma-separated provider order, e.g., coindesk,coinmarketcap"),
) -> None:
    """Fetch and display the latest quote using provider fallback order."""
    import wealth.datasources  # noqa
    from wealth.datasources.registry import get_price_sources
    cfg = get_config()
    all_sources = get_price_sources()
    default_order = [s.strip() for s in os.getenv("WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk").split(",") if s.strip()]
    cli_order = [s.strip() for s in providers.split(",")] if providers else None
    base_order = cli_order or default_order
    sym = asset.strip().upper()
    with session_scope(cfg.db_path) as s:
        preferred = get_asset_preference(s, sym)
    order = []
    if preferred:
        order.append(preferred)
    for name in base_order:
        if name not in order:
            order.append(name)

    last_err = None
    for prov_name in order:
        if prov_name not in all_sources:
            continue
        try:
            src_cls = all_sources[prov_name]
            src = src_cls()  # type: ignore[call-arg]
            q = src.get_quote(sym, quote)
        except Exception as e:
            last_err = e
            continue
        with session_scope(cfg.db_path) as s:
            set_asset_preference(s, sym, src.id())
        typer.echo(f"{q.symbol}/{q.quote_ccy} price={q.price} ts={q.ts.isoformat()} (via {src.id()})")
        return
    msg = f"Failed to fetch quote for {sym} from all providers"
    if last_err:
        msg += f": last error: {last_err}"
    raise typer.Exit(code=1)


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
from .cli.chart import app as chart_app
from .cli.report import app as report_app

app.add_typer(account_app, name="account")
app.add_typer(tx_app, name="tx")
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")
app.add_typer(chart_app, name="chart")
app.add_typer(report_app, name="report")


portfolio_app = typer.Typer(help="Portfolio views")


@portfolio_app.command("summary")
def portfolio_summary(
    as_of: Optional[datetime] = typer.Option(None, "--as-of", help="As-of date/time (ISO); defaults to now"),
    quote: str = typer.Option("USD", "--quote", help="Quote currency for valuation"),
    account_id: Optional[int] = typer.Option(None, "--account-id", help="Limit to a single account"),
) -> None:
    cfg = get_config()
    as_of = as_of or datetime.utcnow()
    with session_scope(cfg.db_path) as s:
        positions, totals = summarize_portfolio(s, as_of=as_of, quote=quote, account_id=account_id)
    if not positions:
        typer.echo("No holdings as of the specified time.")
        raise typer.Exit(code=0)
    typer.echo(f"Portfolio summary as of {as_of.isoformat()} in {quote}:")
    typer.echo("asset  qty                 price           value           cost_open       unrealized      realized")
    for p in positions:
        price_s = f"{p.price}" if p.price is not None else "N/A"
        value_s = f"{p.value}" if p.value is not None else "N/A"
        cost_s = f"{p.cost_open}" if p.cost_open is not None else "N/A"
        unreal_s = f"{p.unrealized_pnl}" if p.unrealized_pnl is not None else "N/A"
        typer.echo(
            f"{p.asset:<5} {p.qty:<18} {price_s:<15} {value_s:<15} {cost_s:<15} {unreal_s:<15} {p.realized_pnl}"
        )
    typer.echo("Totals:")
    typer.echo(
        f"value={totals['value']} cost_open={totals['cost_open']} unrealized={totals['unrealized']} realized={totals['realized']}"
    )


app.add_typer(portfolio_app, name="portfolio")


def main() -> None:
    app()

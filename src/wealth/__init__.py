from __future__ import annotations

import logging
from typing import Optional
from datetime import datetime
import time
import os

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .core.config import get_config
from .db.engine import init_db
from .db.repo import session_scope, upsert_price, list_prices, get_asset_preference, set_asset_preference
from .core.valuation import summarize_portfolio
from wealth.cli.ui import fmt_decimal, fmt_money, colorize_pnl
from wealth.core.context import load_context


app = typer.Typer(help="Wealth CLI — manage crypto transactions and reports.")
console = Console()


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

    price_sources = sorted(get_price_sources().keys())
    import_sources = sorted(get_import_sources().keys())

    pt = Table(title="Price Sources")
    pt.add_column("Name")
    for k in price_sources:
        pt.add_row(k)
    it = Table(title="Import Sources")
    it.add_column("Name")
    for k in import_sources:
        it.add_row(k)
    console.print(pt)
    console.print(it)


app.add_typer(datasource_app, name="datasource")


price_app = typer.Typer(help="Price data commands")


@price_app.command("sync")
def price_sync(
    assets: str = typer.Option(..., "--assets", help="Comma-separated symbols, e.g., BTC,ETH"),
    since: datetime = typer.Option(..., "--since", help="Start date/time (YYYY-MM-DD or ISO)"),
    until: Optional[datetime] = typer.Option(None, "--until", help="End date/time; defaults to now"),
    quote: Optional[str] = typer.Option(None, "--quote", help="Quote currency (defaults to context or config)"),
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
    ctx = load_context()
    quote = quote or ctx.quote or get_config().base_currency
    default_order = [s.strip() for s in (ctx.providers or os.getenv("WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk")).split(",") if s.strip()]
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
    quote: Optional[str] = typer.Option(None, "--quote", help="Quote currency (defaults to context or config)"),
    providers: Optional[str] = typer.Option(None, "--providers", help="Comma-separated provider order, e.g., coindesk,coinmarketcap"),
) -> None:
    """Fetch and display the latest quote using provider fallback order."""
    import wealth.datasources  # noqa
    from wealth.datasources.registry import get_price_sources
    cfg = get_config()
    ctx = load_context()
    quote = quote or ctx.quote or cfg.base_currency
    all_sources = get_price_sources()
    default_order = [s.strip() for s in (ctx.providers or os.getenv("WEALTH_PRICE_PROVIDER_ORDER", "coinmarketcap,coindesk")).split(",") if s.strip()]
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
    quote: Optional[str] = typer.Option(None, "--quote", help="Quote currency (defaults to context or config)"),
    limit: int = typer.Option(20, "--limit", help="Limit number of rows"),
) -> None:
    """Show cached prices from the local DB."""
    cfg = get_config()
    ctx = load_context()
    quote = quote or ctx.quote or cfg.base_currency
    with session_scope(cfg.db_path) as s:
        rows = list_prices(s, asset_symbol=asset, quote_ccy=quote, since=since, limit=limit)
    if not rows:
        typer.echo("No prices found.")
        raise typer.Exit(code=0)
    table = Table(title=f"Prices for {asset}/{quote}")
    table.add_column("Timestamp")
    table.add_column("Close", justify="right")
    for r in rows:
        table.add_row(r.ts.isoformat(), str(r.price))
    console.print(table)


app.add_typer(price_app, name="price")

# Domain subcommands
from .cli.account import app as account_app
from .cli.tx import app as tx_app
from .cli.import_cmd import app as import_app
from .cli.export_cmd import app as export_app
from .cli.chart import app as chart_app
from .cli.report import app as report_app
from .cli.context_cmd import app as context_app
import subprocess
import shutil
import threading
import time as _time
from uvicorn import Config as UvicornConfig, Server as UvicornServer

app.add_typer(account_app, name="account")
app.add_typer(tx_app, name="tx")
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")
app.add_typer(chart_app, name="chart")
app.add_typer(report_app, name="report")
app.add_typer(context_app, name="context")


portfolio_app = typer.Typer(help="Portfolio views")


@portfolio_app.command("summary")
def portfolio_summary(
    as_of: Optional[datetime] = typer.Option(None, "--as-of", help="As-of date/time (ISO); defaults to now"),
    quote: Optional[str] = typer.Option(None, "--quote", help="Quote currency for valuation (defaults to context or config)"),
    account_id: Optional[int] = typer.Option(None, "--account-id", help="Limit to a single account"),
) -> None:
    cfg = get_config()
    ctx = load_context()
    as_of = as_of or datetime.utcnow()
    quote = quote or ctx.quote or cfg.base_currency
    with session_scope(cfg.db_path) as s:
        positions, totals = summarize_portfolio(s, as_of=as_of, quote=quote, account_id=account_id)
    if not positions:
        console.print("[yellow]No holdings as of the specified time.[/yellow]")
        raise typer.Exit(code=0)
    console.print(Panel.fit(f"Portfolio summary as of {as_of.isoformat()} in {quote}", border_style="cyan"))
    table = Table(title="Positions")
    table.add_column("Asset")
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", justify="right")
    table.add_column("Cost Open", justify="right")
    table.add_column("Unrealized", justify="right")
    table.add_column("Realized", justify="right")
    for p in positions:
        price_s = fmt_money(p.price) if p.price is not None else "-"
        value_s = fmt_money(p.value) if p.value is not None else "-"
        cost_s = fmt_money(p.cost_open) if p.cost_open is not None else "-"
        table.add_row(
            p.asset,
            fmt_decimal(p.qty),
            price_s,
            value_s,
            cost_s,
            colorize_pnl(p.unrealized_pnl),
            colorize_pnl(p.realized_pnl),
        )
    console.print(table)
    totals_panel = Panel(
        f"[bold]Totals[/bold]\nValue: {fmt_money(totals['value'])}\nCost Open: {fmt_money(totals['cost_open'])}\nUnrealized: {fmt_money(totals['unrealized'])}\nRealized: {fmt_money(totals['realized'])}",
        border_style="magenta",
    )
    console.print(totals_panel)


app.add_typer(portfolio_app, name="portfolio")


@portfolio_app.command("chart")
def portfolio_chart(
    since: datetime = typer.Option(..., "--since", help="Start date/time (YYYY-MM-DD or ISO)"),
    until: Optional[datetime] = typer.Option(None, "--until", help="End date/time; defaults to now"),
    quote: Optional[str] = typer.Option(None, "--quote", help="Quote currency for valuation (defaults to context or config)"),
    account_id: Optional[int] = typer.Option(None, "--account-id", help="Limit to a single account"),
) -> None:
    """Render a terminal line chart of portfolio value over time."""
    import plotext as plt
    from wealth.core.valuation import summarize_portfolio
    from datetime import timedelta

    cfg = get_config()
    ctx = load_context()
    quote = quote or ctx.quote or cfg.base_currency
    until = until or datetime.utcnow()
    xs = []
    ys = []
    with session_scope(cfg.db_path) as s:
        cur = since
        while cur <= until:
            positions, totals = summarize_portfolio(s, as_of=cur, quote=quote, account_id=account_id)
            xs.append(cur.strftime('%Y-%m-%d'))
            ys.append(float(totals["value"]))
            cur = cur + timedelta(days=1)
    if not ys:
        console.print("[yellow]No data available for the requested range.[/yellow]")
        raise typer.Exit(code=0)
    plt.clear_figure()
    plt.date_form('Y-m-d')
    plt.plot(xs, ys, marker='dot')
    plt.title(f"Portfolio Value ({quote})")
    plt.show()

def main() -> None:
    app()


@app.command("api")
def run_api(port: int = typer.Option(8001, "--port"), host: str = typer.Option("127.0.0.1", "--host")) -> None:
    cfg = get_config()
    init_db(cfg.db_path)
    from wealth.api.server import app as fastapi_app
    server = UvicornServer(UvicornConfig(fastapi_app, host=host, port=port, log_level="info"))
    server.run()


@app.command("ui")
def run_ui(
    ui_path: str = typer.Option("src/wealth/ui", "--ui-path", help="Path to Next.js UI project"),
    api_port: int = typer.Option(8001, "--api-port"),
    api_host: str = typer.Option("127.0.0.1", "--api-host"),
    ui_cmd: str = typer.Option("npm run dev", "--ui-cmd", help="Command to start UI dev server"),
) -> None:
    """Start the FastAPI backend and Next.js dev server."""
    cfg = get_config()
    init_db(cfg.db_path)

    from wealth.api.server import app as fastapi_app
    server = UvicornServer(UvicornConfig(fastapi_app, host=api_host, port=api_port, log_level="info"))

    # Start backend in a separate thread
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    _time.sleep(0.5)
    console.print(Panel.fit(f"API running at http://{api_host}:{api_port} (docs at /docs)", border_style="green"))

    # Start Next.js UI
    if not shutil.which(ui_cmd.split()[0]):
        console.print("[yellow]Note: UI command not found. Please run the UI manually.[/yellow]")
        console.print(f"cd {ui_path} && {ui_cmd}")
        console.print("Backend API remains running above.")
        t.join()
        return

    env = dict(**os.environ)
    env["NEXT_PUBLIC_API_BASE"] = f"http://{api_host}:{api_port}"
    try:
        proc = subprocess.Popen(ui_cmd, cwd=ui_path, shell=True, env=env)
        console.print(Panel.fit(f"UI starting with {ui_cmd} in {ui_path}. NEXT_PUBLIC_API_BASE={env['NEXT_PUBLIC_API_BASE']}", border_style="cyan"))
        proc.wait()
    except KeyboardInterrupt:
        pass
    finally:
        # Server will stop when process exits; thread is daemon
        console.print("[yellow]Shutting down...[/yellow]")

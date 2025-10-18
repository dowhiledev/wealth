Wealth CLI
===========

CLI-based wealth management tool focused on crypto first (extensible to others).

Quick Start
-----------

- Ensure Python 3.11+
- Install deps (uv):
  - `uv sync` or install extras if needed
- Configure `.env` (copy `.env.example`):
  - `COINMARKETCAP_API_KEY=...`
  - Optional: `COINMARKETCAP_BASE_URL=https://sandbox-api.coinmarketcap.com`
  - Optional: `WEALTH_DB_PATH=wealth.db`, `WEALTH_BASE_CURRENCY=USD`

CLI Usage
---------

- Help: `PYTHONPATH=src uv run python -m wealth --help`
- Init DB: `PYTHONPATH=src uv run python -m wealth init`

Accounts
- Add: `PYTHONPATH=src uv run python -m wealth account add --name Main --type exchange`
- List: `PYTHONPATH=src uv run python -m wealth account list`

Transactions
- Add: `PYTHONPATH=src uv run python -m wealth tx add --account-id 1 --asset BTC --side buy --qty 0.1 --price-quote 30000 --total-quote 3000`
- List: `PYTHONPATH=src uv run python -m wealth tx list --account-id 1`

Prices (CoinMarketCap)
- Quote: `PYTHONPATH=src uv run python -m wealth price quote --asset BTC`
- Sync OHLCV: `PYTHONPATH=src uv run python -m wealth price sync --assets BTC --since 2024-01-01 --quote USD --interval 1d`

Import/Export CSV
- Import: `PYTHONPATH=src uv run python -m wealth import csv --file tx.csv --account-id 1`
- Export: `PYTHONPATH=src uv run python -m wealth export csv --out exported.csv --account-id 1`

Portfolio
- Summary: `PYTHONPATH=src uv run python -m wealth portfolio summary --quote USD`

Charts & Report
- Allocation chart: `PYTHONPATH=src uv run python -m wealth chart allocation --out reports/alloc.png`
- Value chart: `PYTHONPATH=src uv run python -m wealth chart value --out reports/value.png --since 2024-01-01`
- PnL chart: `PYTHONPATH=src uv run python -m wealth chart pnl --out reports/pnl.png --since 2024-01-01`
- PDF report: `PYTHONPATH=src uv run python -m wealth report generate --out reports/wealth_report.pdf`

Testing
-------

- Run test suite: `uv run pytest -q`

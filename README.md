WealthOS
========

WealthOS is a modern, privacy‑first portfolio tracker with a fast CLI, a clean web UI (Next.js), and extensible data sources. It focuses on crypto first and stays flexible for other assets.

Highlights
---------

- Clean dashboard with KPIs, allocation, P&L over time, top holdings, and recent activity
- Multi‑account filtering, dark mode, centered responsive layout
- Powerful transactions tables (edit in dialog, batch delete, sort/filter, column visibility)
- Robust API (FastAPI) and CLI (Typer) for full control and automation
- CSV import/export, charts, and PDF reports

Quick Start
-----------

Prereqs: Python 3.11+, Node.js 18+ (for building the UI)

1) Install Python deps (using uv)
- `uv sync`

2) Configure environment
- Copy `.env.example` to `.env`
- Set `COINMARKETCAP_API_KEY=...` (optional, for prices)
- Optionals: `WEALTH_DB_PATH=wealth.db`, `WEALTH_BASE_CURRENCY=USD`

3) Initialize the DB
- `uv run wealth init`
- Optionally seed demo data: `uv run wealth seed`

4) Run API + UI
- Production UI (recommended): `uv run wealth ui`
  - Force rebuild if needed: `... wealth ui --build`
  - Custom UI/API ports: `... wealth ui --ui-port 4000 --api-port 8002`
- Dev UI: `uv run wealth ui --dev`

CLI Essentials
--------------

- Help: `uv run wealth --help`
- Accounts: `uv run wealth account add/list/update/remove`
- Transactions: `uv run wealth tx add/list/update/remove`
- Prices: `uv run wealth price quote|sync`
- Portfolio: `uv run wealth portfolio summary|chart`
- CSV: `uv run wealth import csv ...` / `uv run wealth export csv ...`
- Reports: `uv run wealth report generate`

Web UI Overview
---------------

- Dashboard: KPIs, Portfolio Allocation, Realized P&L, Top Holdings by Value, Recent Activity
- Accounts: Grid of accounts; click to open an account view
- Account View: KPIs scoped to that account, allocation, P&L, volume, and a full transactions table
- Transactions: Full DataTable with edit, delete, batch operations, filtering, column visibility

Design
------

- Centered content on large screens; clean spacing; dark mode toggle in the sidebar
- Accessible controls and meaningful labels (e.g., “Trade Volume (Buy vs Sell)”, “Recent Activity”)

Development
-----------

- Run tests: `uv run pytest -q`
- Lint/typecheck (suggested): ruff/mypy/eslint if you use them locally

Licensing & Contributing
------------------------

- License: MIT (see LICENSE)
- Contributions welcome — read CONTRIBUTING.md for guidelines

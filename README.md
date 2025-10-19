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

Install
-------

- Python 3.11+ required
- Optional for UI: Node.js 18+ (only needed to build/run the Next.js UI)

From PyPI (recommended):
- `pip install wealth-os`
- Or with pipx: `pipx install wealth-os` (great for a standalone CLI)

From source (developers):
- `uv sync` to install local deps into the virtualenv

Quick Start
-----------

1) Configure environment
- Copy `.env.example` to `.env`
- Set `COINMARKETCAP_API_KEY=...` and/or `COINDESK_API_KEY=...` for price data (optional)
- Optionals: `WEALTH_DB_PATH=wealth.db`, `WEALTH_BASE_CURRENCY=USD`

2) Initialize the DB
- `wealth init`
- Seed demo data (optional): `wealth seed`

3) Run API + UI
- Production UI: `wealth ui`
  - Force rebuild if needed: `wealth ui --build`
  - Custom ports: `wealth ui --ui-port 4000 --api-port 8002`
- Dev UI: `wealth ui --dev`

CLI Essentials
--------------

- Help: `wealth --help`
- Accounts: `wealth account add|list|update|remove`
- Transactions: `wealth tx add|list|update|remove`
- Prices: `wealth price quote|sync`
- Portfolio: `wealth portfolio summary|chart`
- CSV: `wealth import csv ...` / `wealth export csv ...`
- Reports: `wealth report generate`

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

Publish to PyPI
---------------

Maintainers: steps to cut a release.

- Bump `version` in `pyproject.toml` and update changelog if applicable
- Build artifacts:
  - `python -m pip install --upgrade build twine`
  - `python -m build`  # creates `dist/*.tar.gz` and `dist/*.whl`
  - `twine check dist/*`
- Optional: TestPyPI smoke test
  - `twine upload -r testpypi dist/*`
  - `pip install -i https://test.pypi.org/simple wealth-os`
- Publish to PyPI
  - `twine upload dist/*`

After install, the CLI entry point is `wealth` (or run `python -m wealth_os`).

Licensing & Contributing
------------------------

- License: MIT (see LICENSE)
- Contributions welcome — read CONTRIBUTING.md for guidelines

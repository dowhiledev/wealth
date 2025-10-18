# AGENT Guide — Wealth CLI, API, and UI

This repository hosts a CLI wealth manager (Python), a REST API (FastAPI), and a Next.js UI (shadcn‑styled). This guide explains how an AI assistant (and humans) should work in this repo safely and efficiently.

If you only need a quick start:

- Install deps: `uv sync` (Python), `cd src/wealth/ui && npm install` (Node)
- Seed data: `uv run python -m wealth seed --reset --days 60`
- Start UI + API: `uv run python -m wealth ui`
- CLI help: `uv run python -m wealth --help`

---

## Project Overview

- CLI entrypoint: `wealth` (Typer)
- Database: SQLite via SQLModel (no Alembic). Tables created on demand.
- API: FastAPI (Uvicorn) under `src/wealth/api/server.py`
- UI: Next.js (shadcn) under `src/wealth/ui` (dashboard shell)
- Price providers: CoinMarketCap (pro), Coindesk legacy (CryptoCompare)
- Providers fallback + per‑asset preference persisted

---

## Conventions For AI Assistants

- Use ripgrep for search: `rg` (fast, concise)
- Use uv for Python workflow:
  - Run: `uv run python -m wealth ...`
  - Install: `uv add <pkg>` or `uv sync`
- Keep patches minimal and focused. Prefer surgical changes over refactors.
- When adding code, match existing style; avoid introducing new formatters/linters.
- Never commit credentials. `.env` is used locally; API keys read from env at runtime.
- Prefer existing patterns and folders; do not move files unless necessary.
- When adding DB models in `src/wealth/db/models.py`, remember there’s no migrations. Ensure new tables work with `create_all`.
- Add tests where it’s natural (under `tests/`) and keep them fast.

---

## Repository Map

- `src/wealth/__init__.py` — CLI (Typer) commands: init, config, datasource, price, account, tx, import, export, chart, report, portfolio, api, ui, seed
- `src/wealth/core/` — config, valuation, context (CLI defaults)
- `src/wealth/db/` — engine, models (SQLModel), repo helpers (CRUD, queries)
- `src/wealth/datasources/` — base protocols, registry, providers (coinmarketcap, coindesk_legacy), generic CSV importer
- `src/wealth/io/` — charts (matplotlib/seaborn), pdf_report (reportlab)
- `src/wealth/api/server.py` — FastAPI app and REST routes (accounts, transactions, portfolio summary, stats)
- `src/wealth/cli/` — CLI subcommands, rich UI helpers
- `src/wealth/ui/` — Next.js app (shadcn dashboard shell + pages)
- `tests/` — unit/smoke tests for repo, valuation, CSV import/export

---

## Setup & Environment

- Python 3.11+
- Install Python deps: `uv sync`
- Node (for UI), then UI deps: `cd src/wealth/ui && npm install`
- `.env` keys (examples in `.env.example`):
  - `COINMARKETCAP_API_KEY` (required for CMC)
  - `COINMARKETCAP_BASE_URL` (optional; https://pro-api.coinmarketcap.com by default; scheme auto‑normalized)
  - `COINDESK_API_KEY` (required for CryptoCompare)
  - `WEALTH_DB_PATH` (default `wealth.db`)
  - `WEALTH_BASE_CURRENCY` (default `USD`)
  - `WEALTH_PRICE_PROVIDER_ORDER` (e.g. `coindesk,coinmarketcap`)

---

## Common Commands

- Initialize DB: `uv run python -m wealth init`
- Seed with mock data: `uv run python -m wealth seed --reset --days 60`
- Context defaults: `uv run python -m wealth context set account_id 1`
- Accounts CRUD: `wealth account add|list|edit|rm`
- Transactions CRUD: `wealth tx add|list|edit|rm`
- Import CSV: `wealth import csv --file tx.csv --account-id <id>` (or use context defaults)
- Export CSV: `wealth export csv --out exported.csv`
- Price quote: `wealth price quote --asset BTC [--providers ...]`
- Sync prices: `wealth price sync --assets BTC,ETH --since 2024-01-01 [--providers ...]`
- Portfolio summary: `wealth portfolio summary`
- Terminal chart: `wealth portfolio chart --since 2024-01-01`
- API: `wealth api --port 8001` (docs at `/docs`)
- UI + API: `wealth ui` (starts both; sets `NEXT_PUBLIC_API_BASE` for UI)
- Tests: `uv run pytest -q`

---

## Database Guidelines (No Migrations)

- Models live in `src/wealth/db/models.py` (SQLModel). No Alembic — new tables are created via `SQLModel.metadata.create_all`.
- Keep changes backward‑compatible if possible; avoid renaming columns.
- When adding relationships, prefer explicit foreign keys and index fields; relationships were omitted in v1 for simplicity.
- Session helper (`session_scope`) sets `expire_on_commit=False` to avoid detached instance pitfalls in CLI rendering.

---

## Providers & Pricing

- Providers implement `PriceDataSource` in `src/wealth/datasources/base.py` and register via `registry.register_price_source`.
- Existing providers:
  - `coinmarketcap` — requires `COINMARKETCAP_API_KEY`; OHLCV historical may require paid tier.
  - `coindesk` (CryptoCompare) — requires `COINDESK_API_KEY`; supports daily `histoday`.
- Fallback order can be specified per command (`--providers`) or via context/env (`context set providers`, `WEALTH_PRICE_PROVIDER_ORDER`).
- Per‑asset provider preference is persisted in `AssetPreference` and used first in subsequent calls.

---

## REST API Conventions

- Location: `src/wealth/api/server.py`
- Core routes:
  - Accounts: `GET/POST /accounts`, `PUT/DELETE /accounts/{id}`
  - Transactions: `GET/POST /transactions`, `PUT/DELETE /transactions/{tx_id}`
  - Portfolio summary: `GET /portfolio/summary?quote=USD&account_id=...`
  - Stats: `GET /stats`
- Pydantic models mirror SQLModel fields; Decimals are returned as numbers (UI formats them).

---

## UI Guidelines (Next.js + shadcn)

- UI root: `src/wealth/ui`
- Dashboard shell (sidebar/header) under `/app/dashboard` using shadcn block structure.
- Data access via `src/wealth/ui/lib/api.ts` using `NEXT_PUBLIC_API_BASE`.
- Use shadcn components for Cards, Tables, Charts (Recharts). Respect CSS variables (old‑money palette). Keep dark mode legible.
- Add new pages under `/dashboard/*`. Reuse existing forms/tables for CRUD.

---

## Testing & Quality

- Run tests: `uv run pytest -q`
- Existing tests: repo CRUD, valuation (FIFO), CSV import/export.
- Add unit tests for new repo helpers and APIs where practical.
- Keep tests data‑local (use the tmp DB fixture). Don’t hit external APIs in tests.

---

## Contribution Checklist (AI‑friendly)

1. Search context with `rg` and skim relevant files (max 250 lines per view).
2. Make a small plan (what files change, what functions to add).
3. Edit with minimal diffs using the patch tool; avoid noisy refactors.
4. Prefer extending existing commands/APIs over creating parallel copies.
5. Verify locally: run the specific command or target test; optionally run `pytest -q`.
6. Document new flags/endpoints briefly in this guide (or README) if user‑facing.

---

## Common Recipes

- Add a CLI command
  - Place it in `src/wealth/__init__.py` (or a submodule under `src/wealth/cli/` and import it).
  - Use Typer patterns already in the file; keep output styled with Rich.

- Add a new provider
  - Create `src/wealth/datasources/<provider>.py`, implement `PriceDataSource`, register via `@register_price_source`.
  - Read API keys from env; normalize base URLs (ensure scheme); add to `/datasource list`.

- Add an API endpoint
  - Define Pydantic models near the route; reuse repo functions.
  - Ensure CORS is OK for localhost dev.

- Add a UI panel/page
  - Add a component in `src/wealth/ui/components/` and a route under `/app/dashboard/*`.
  - Fetch data via `lib/api.ts` or `fetch(NEXT_PUBLIC_API_BASE + ...)`.
  - Use shadcn Card/Table/Chart components; align colors with CSS variables.

---

## Troubleshooting

- Quote fails with CMC 403 — your plan may not include OHLCV; use `--providers coindesk,coinmarketcap` or set `COINDESK_API_KEY`.
- UI can’t reach API — ensure `wealth ui` set `NEXT_PUBLIC_API_BASE` and API is serving (`/health`).
- DetachedInstanceError — sessions are configured to avoid this. If you see it, ensure printing happens within a session or copy values first.
- DB changes not visible — run `wealth init` or re‑seed; tables are created on demand.


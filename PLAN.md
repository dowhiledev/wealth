# Wealth CLI — Prioritized Execution Plan

This plan reflects your inputs:
- No Alembic (use SQLModel + SQLite `create_all` for schema).
- Personal tool: ignore security/privacy considerations.
- CoinMarketCap (CMC) as the initial data source for crypto prices; API key from `.env` (`COINMARKETCAP_API_KEY`).
- Project already bootstrapped with `uv`; add dependencies as needed.

Phases are ordered by impact and dependency. Each phase includes a summary, checklist, and acceptance criteria. No timelines are included.

---

## Phase 1 — Foundations & CLI Skeleton

Summary
- Establish CLI entrypoint and project structure; load configuration from `.env`; wire up logging; ensure a local SQLite database path is resolved.

Checklist
- Add baseline package structure under `src/wealth/` (commands, core, db, datasources, io).
- Implement Typer app with grouped commands (`wealth` root with subcommands scaffolded).
- Load `.env` using `python-dotenv`; read `COINMARKETCAP_API_KEY` and default settings (DB path, base currency = `USD`).
- Initialize SQLite engine (SQLModel) with pragmas and `create_all` on `wealth init`.
- Add minimal logging (INFO default) and a global config object.
- Confirm packaging hook in `pyproject.toml` (`wealth = "wealth:main"`).

Acceptance Criteria
- `wealth --help` shows root command and subcommands.
- `wealth init` creates the SQLite file at the configured path and reports success.
- `wealth config show` prints loaded configuration including whether `COINMARKETCAP_API_KEY` is detected.

---

## Phase 2 — Database Models & Persistence (No Migrations)

Summary
- Define core SQLModel models and repository helpers; create tables on demand without Alembic.

Checklist
- Create models: `Account`, `Asset`, `Transaction`, `Price`, `ImportBatch` (optional).
- Provide enums: `AccountType` (exchange, wallet), `TxSide` (buy, sell, transfer, stake, reward, fee).
- Add sensible indices (by timestamp, account, asset) and constraints.
- Implement repository/service helpers for CRUD and listing with filters + pagination.
- Ensure `wealth init` (or first DB touch) runs `SQLModel.metadata.create_all`.

Acceptance Criteria
- Adding and listing a record for each entity works via programmatic call (exercised in later CLI phase).
- Tables exist and persist to the configured SQLite file.

---

## Phase 3 — DataSource Abstractions & Registry

Summary
- Create pluggable interfaces for price providers and CSV transaction importers; register available sources.

Checklist
- Define `PriceDataSource` interface: `id()`, `get_quote(symbol, quote='USD')`, `get_ohlcv(symbol, start, end, interval='1d')`, and asset metadata lookup (symbol↔id mapping).
- Define `TxImportSource` interface: `id()`, `supports_csv()`, `parse_csv(path, options) -> list[NormalizedTx]`.
- Create `NormalizedTx` Pydantic model for parsed rows.
- Implement a simple registry and `wealth datasource list` command that shows available providers (e.g., `coinmarketcap` for prices; `generic_csv` for tx import).

Acceptance Criteria
- `wealth datasource list` prints at least `coinmarketcap` (price) and `generic_csv` (tx import).
- Interfaces compile and are referenced by later phases.

---

## Phase 4 — CoinMarketCap Integration (Price Provider)

Summary
- Implement CMC client and provider that pulls spot and historical prices and stores them in the `prices` table.

Checklist
- Add a small HTTP client using `requests` with API key header.
- Endpoints: `/v1/cryptocurrency/quotes/latest` and `/v2/cryptocurrency/ohlcv/historical`.
- Implement symbol-to-CMC-ID resolution with simple in-memory cache.
- CLI: `wealth price sync --assets BTC,ETH --since 2021-01-01 --quote USD [--interval 1d]`.
- Persist prices idempotently (upsert unique on asset, quote, timestamp).
- Handle rate limiting with respectful delays and clear error messages.

Acceptance Criteria
- Running `wealth price sync` stores prices in DB and reports counts inserted/updated.
- `wealth price show --asset BTC --since ...` prints recent cached prices from DB.

---

## Phase 5 — CRUD CLI for Accounts & Transactions

Summary
- Expose user-friendly CLI to add, edit, delete, and list accounts and transactions.

Checklist
- Commands: `wealth account add|list|edit|rm`; `wealth tx add|edit|rm|list` with filters (`--account`, `--asset`, `--since`, `--until`).
- Interactive prompts for required fields; parse decimals and timestamps robustly.
- Auto-create assets on demand when adding a transaction.
- Validation of `TxSide` and fee handling.

Acceptance Criteria
- Users can add an account and multiple transactions, list them, edit a field, and delete.
- Output tables render cleanly (using Typer/Rich or similar) and reflect persisted state.

---

## Phase 6 — CSV Import & Export

Summary
- Provide generic CSV importer with configurable column mapping; export transactions in a canonical schema.

Checklist
- Define canonical CSV columns: `timestamp, account, asset, side, qty, price_quote, quote_ccy, fee_qty, fee_asset, note, tags`.
- Implement `generic_csv` importer: configurable mapping, robust datetime/number parsing, and dry-run mode.
- Dedupe strategy: `(datasource, external_id | hash(row))` and record `import_batch_id`.
- CLI: `wealth import csv --source generic --file path.csv [--mapping mapping.json --dry-run]`.
- CLI: `wealth export csv --out tx.csv [--account ... --since ...]`.

Acceptance Criteria
- Importing a sample CSV reports rows imported/skipped and persists transactions; dry-run performs no writes.
- Export creates a CSV that can be re-imported with no data loss (round-trip test on small sample).

---

## Phase 7 — Valuation & Portfolio Summary

Summary
- Compute holdings and portfolio value using cached prices; basic realized/unrealized PnL with FIFO lots.

Checklist
- Holdings by asset/account from transactions (buys, sells, transfers, rewards, fees).
- Valuation at an as-of time using last known price.
- Realized PnL using FIFO; Unrealized PnL from current holdings.
- CLI: `wealth portfolio summary [--as-of YYYY-MM-DD --quote USD]`.

Acceptance Criteria
- CLI prints totals and per-asset positions (qty, price, value, cost basis, PnL).
- Calculations are consistent on deterministic sample data.

---

## Phase 8 — Charts & PDF Reports

Summary
- Generate charts (allocation, portfolio value over time, realized PnL) and assemble a PDF report.

Checklist
- Charts via seaborn/matplotlib; save PNGs under `reports/`.
- PDF via ReportLab combining title page, KPI table, and embedded charts.
- CLI: `wealth chart allocation|value|pnl --out path.png` and `wealth report generate --out report.pdf [--sections ...]`.

Acceptance Criteria
- PNG charts are generated at requested paths with sensible defaults and labels.
- PDF report is created, includes selected sections and embeds generated charts.

---

## Phase 9 — Polish & Documentation

Summary
- Smooth developer and user experience, finalize dependencies, and document commands and configuration.

Checklist
- Update `README.md` with setup, `.env` keys, and command examples.
- Provide `.env.example` mirroring `COINMARKETCAP_API_KEY` and default settings.
- Ensure `pyproject.toml` lists required dependencies (e.g., `python-dotenv`, `reportlab`).
- Add a small set of smoke tests for key flows (optional but recommended).

Acceptance Criteria
- README instructions allow a new user to: init DB → add a transaction → sync prices → view portfolio → generate a chart/PDF.
- `wealth --help` output is clear and organized; version is displayed with `wealth --version`.

---

## Anticipated Dependencies To Add

- `python-dotenv` (load `.env`).
- `reportlab` (PDF generation).
- Optional: `rich` (pretty CLI tables) if desired beyond Typer defaults.

All other required packages are already present (`typer`, `sqlmodel`, `pandas`, `requests`, `seaborn`/`matplotlib`).


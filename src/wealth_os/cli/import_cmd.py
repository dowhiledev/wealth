from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from wealth_os.core.config import get_config
from wealth_os.core.context import load_context
from wealth_os.datasources.generic_csv import GenericCSVImportSource
from wealth_os.db.repo import (
    session_scope,
    create_transaction,
    create_import_batch,
    update_import_batch_summary,
    find_tx_by_external_id,
    find_tx_by_tx_hash,
)


app = typer.Typer(help="Import data")


@app.command("csv")
def import_csv(
    file: Path = typer.Option(
        ..., "--file", exists=True, readable=True, help="Path to CSV file"
    ),
    account_id: Optional[int] = typer.Option(
        None,
        "--account-id",
        help="Account id to assign to all rows (defaults to context)",
    ),
    mapping_file: Optional[Path] = typer.Option(
        None, "--mapping-file", help="JSON file mapping canonical->csv columns"
    ),
    datasource: Optional[str] = typer.Option(
        None,
        "--datasource",
        help="Datasource label to record (defaults to context or generic_csv)",
    ),
    dedupe_by: str = typer.Option(
        "external_id", "--dedupe-by", help="external_id|tx_hash|none"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Parse and validate without writing"
    ),
):
    cfg = get_config()
    mapping = None
    ctx = load_context()
    account_id = account_id or ctx.account_id
    datasource = datasource or ctx.datasource or "generic_csv"
    if account_id is None:
        raise typer.BadParameter(
            "--account-id is required (set via --account-id or `wealth context set account_id <id>`)"
        )
    if mapping_file:
        with open(mapping_file, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            if not isinstance(mapping, dict):
                raise typer.BadParameter("mapping-file must contain a JSON object")

    src = GenericCSVImportSource()
    parsed = src.parse_csv(str(file), options={"mapping": mapping or {}})

    inserted = 0
    skipped = 0

    if dry_run:
        typer.echo(f"Dry-run: parsed {len(parsed)} rows from {file}")
        raise typer.Exit(code=0)

    with session_scope(cfg.db_path) as s:
        batch = create_import_batch(
            s, datasource=datasource, source_file=str(file), summary=None
        )
        for row in parsed:
            # dedupe checks
            if dedupe_by == "external_id" and row.external_id:
                if find_tx_by_external_id(
                    s, datasource=datasource, external_id=row.external_id
                ):
                    skipped += 1
                    continue
            if dedupe_by == "tx_hash" and row.tx_hash:
                if find_tx_by_tx_hash(s, tx_hash=row.tx_hash):
                    skipped += 1
                    continue

            create_transaction(
                s,
                ts=row.ts,
                account_id=account_id,
                asset_symbol=row.asset_symbol,
                side=row.side,
                qty=row.qty,
                price_quote=row.price_quote,
                total_quote=row.total_quote,
                quote_ccy=row.quote_ccy,
                fee_qty=row.fee_qty,
                fee_asset=row.fee_asset,
                note=row.note,
                tx_hash=row.tx_hash,
                external_id=row.external_id,
                datasource=datasource,
                import_batch_id=batch.id,
                tags=row.tags,
            )
            inserted += 1
        update_import_batch_summary(
            s,
            batch.id,
            summary=f"Inserted {inserted}, skipped {skipped} (dedupe_by={dedupe_by})",
        )
    typer.echo(f"Imported {inserted} rows, skipped {skipped} from {file}")

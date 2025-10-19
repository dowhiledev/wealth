import csv
from pathlib import Path

from typer.testing import CliRunner

from wealth_os import app as wealth_app
from wealth_os.core.config import get_config
from wealth_os.db.repo import session_scope, list_accounts


def test_import_export_roundtrip(tmp_path: Path, tmp_db_path):
    runner = CliRunner()
    cfg = get_config()

    # init DB
    r = runner.invoke(wealth_app, ["init"])
    assert r.exit_code == 0

    # add account
    r = runner.invoke(
        wealth_app,
        [
            "account",
            "add",
            "--name",
            "CSVAcc",
            "--type",
            "exchange",
        ],
    )
    assert r.exit_code == 0

    # determine account id
    with session_scope(cfg.db_path) as s:
        accs = list_accounts(s)
        acc_id = [a for a in accs if a.name == "CSVAcc"][0].id

    # create CSV file with canonical columns
    csv_path = tmp_path / "sample.csv"
    headers = [
        "timestamp",
        "account",
        "asset",
        "side",
        "qty",
        "price_quote",
        "total_quote",
        "quote_ccy",
        "fee_qty",
        "fee_asset",
        "note",
        "tags",
        "tx_hash",
        "external_id",
        "datasource",
    ]
    rows = [
        [
            "2024-01-01T10:00:00",
            "CSVAcc",
            "BTC",
            "buy",
            "0.1",
            "30000",
            "3000",
            "USD",
            "",
            "",
            "",
            "demo",
            "",
            "ext-1",
            "generic_csv",
        ],
        [
            "2024-01-02T10:00:00",
            "CSVAcc",
            "ETH",
            "buy",
            "1.0",
            "2000",
            "2000",
            "USD",
            "",
            "",
            "",
            "demo",
            "",
            "ext-2",
            "generic_csv",
        ],
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)

    # import
    r = runner.invoke(
        wealth_app,
        [
            "import",
            "csv",
            "--file",
            str(csv_path),
            "--account-id",
            str(acc_id),
            "--dedupe-by",
            "external_id",
        ],
    )
    assert r.exit_code == 0

    # export
    out = tmp_path / "export.csv"
    r = runner.invoke(
        wealth_app,
        [
            "export",
            "csv",
            "--out",
            str(out),
            "--account-id",
            str(acc_id),
        ],
    )
    assert r.exit_code == 0

    # verify export lines
    with open(out, "r", encoding="utf-8") as f:
        lines = f.readlines()
    assert len(lines) >= 3  # header + 2 rows

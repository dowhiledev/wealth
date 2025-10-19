from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

from .base import NormalizedTx
from .registry import register_import_source
from wealth_os.db.models import TxSide


CANONICAL_COLUMNS = [
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


SIDE_MAP = {
    "buy": TxSide.buy,
    "sell": TxSide.sell,
    "transfer_in": TxSide.transfer_in,
    "transfer-out": TxSide.transfer_out,
    "transfer_out": TxSide.transfer_out,
    "stake": TxSide.stake,
    "reward": TxSide.reward,
    "fee": TxSide.fee,
}


def _to_decimal(x: Any) -> Optional[Decimal]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    return Decimal(s)


@register_import_source
class GenericCSVImportSource:
    """Generic CSV importer.

    Options:
      - mapping: dict canonical_key -> csv_column_name
      - encoding: str (optional)
      - delimiter: str (optional)
    """

    @classmethod
    def id(cls) -> str:
        return "generic_csv"

    @classmethod
    def supports_csv(cls) -> bool:
        return True

    def parse_csv(
        self, path: str, options: Optional[Dict[str, Any]] = None
    ) -> List[NormalizedTx]:
        options = options or {}
        mapping: Dict[str, str] = options.get("mapping", {})
        encoding: Optional[str] = options.get("encoding")
        delimiter: Optional[str] = options.get("delimiter")

        # Default mapping assumes canonical column names present in the CSV
        try:
            df = pd.read_csv(
                path,
                dtype=str,
                usecols=lambda c: True,  # read all cols; we subset later
                encoding=encoding or "utf-8",
                sep=delimiter or ",",
                keep_default_na=False,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to read CSV: {e}")

        out: List[NormalizedTx] = []
        for _, row in df.iterrows():

            def get(col_key: str) -> Optional[str]:
                col_name = mapping.get(col_key, col_key)
                if col_name not in row:
                    return None
                val = row[col_name]
                if isinstance(val, str):
                    val = val.strip()
                return val if val != "" else None

            ts_raw = get("timestamp")
            if not ts_raw:
                raise RuntimeError("Missing required 'timestamp' column")
            try:
                ts = pd.to_datetime(ts_raw, utc=False).to_pydatetime()
                if getattr(ts, "tzinfo", None) is not None:
                    ts = ts.replace(tzinfo=None)
            except Exception:
                raise RuntimeError(f"Failed to parse timestamp: {ts_raw}")

            asset = get("asset")
            if not asset:
                raise RuntimeError("Missing required 'asset' column")

            side_raw = (get("side") or "").lower()
            if side_raw not in SIDE_MAP:
                raise RuntimeError(f"Unsupported side: {side_raw}")
            side = SIDE_MAP[side_raw]

            qty = _to_decimal(get("qty"))
            if qty is None:
                raise RuntimeError("Missing or invalid 'qty'")

            price_quote = _to_decimal(get("price_quote"))
            total_quote = _to_decimal(get("total_quote"))
            fee_qty = _to_decimal(get("fee_qty"))

            nt = NormalizedTx(
                ts=ts,
                account=get("account"),
                asset_symbol=str(asset).upper(),
                side=side,
                qty=qty,
                price_quote=price_quote,
                total_quote=total_quote,
                quote_ccy=(get("quote_ccy") or "USD").upper(),
                fee_qty=fee_qty,
                fee_asset=(get("fee_asset") or None),
                note=get("note"),
                tags=get("tags"),
                tx_hash=get("tx_hash"),
                external_id=get("external_id"),
                datasource=get("datasource"),
            )
            out.append(nt)
        return out

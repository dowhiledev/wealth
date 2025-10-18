from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import NormalizedTx, TxImportSource
from .registry import register_import_source


@register_import_source
class GenericCSVImportSource:
    """Generic CSV importer stub.

    Phase 3: register and list; parsing implemented in the CSV phase.
    """

    @classmethod
    def id(cls) -> str:
        return "generic_csv"

    @classmethod
    def supports_csv(cls) -> bool:
        return True

    def parse_csv(self, path: str, options: Optional[Dict[str, Any]] = None) -> List[NormalizedTx]:
        raise NotImplementedError("Generic CSV parsing will be implemented in the CSV phase")


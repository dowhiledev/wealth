from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_DB_PATH = "wealth.db"


@dataclass(frozen=True)
class Config:
    db_path: str
    base_currency: str


def _resolve_db_path() -> str:
    configured = os.getenv("WEALTH_DB_PATH")
    path = Path(configured) if configured else Path(DEFAULT_DB_PATH)
    path = path.expanduser()
    # Ensure parent exists for nested paths
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(path)


@lru_cache(maxsize=1)
def get_config() -> Config:
    # Load .env once on first access
    load_dotenv(override=False)
    return Config(
        db_path=_resolve_db_path(),
        base_currency=os.getenv("WEALTH_BASE_CURRENCY", "USD"),
    )

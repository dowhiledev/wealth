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
    coinmarketcap_api_key: str | None
    coinmarketcap_base_url: str


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
    # Sandbox toggle and base URL
    use_sandbox = os.getenv("COINMARKETCAP_USE_SANDBOX", "false").lower() in {"1", "true", "yes"}
    base_url = os.getenv(
        "COINMARKETCAP_BASE_URL",
        "https://sandbox-api.coinmarketcap.com" if use_sandbox else "https://pro-api.coinmarketcap.com",
    )

    return Config(
        db_path=_resolve_db_path(),
        base_currency=os.getenv("WEALTH_BASE_CURRENCY", "USD"),
        coinmarketcap_api_key=os.getenv("COINMARKETCAP_API_KEY"),
        coinmarketcap_base_url=base_url,
    )

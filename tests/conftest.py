from pathlib import Path

import pytest

from wealth_os.db.engine import init_db
from wealth_os.core.config import get_config


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture(autouse=True)
def set_db_env(monkeypatch, tmp_db_path: Path):
    # Point CLI/config to a temp DB path for all tests
    monkeypatch.setenv("WEALTH_DB_PATH", str(tmp_db_path))
    # Clear cached config so new env is used per test
    try:
        get_config.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass
    init_db(str(tmp_db_path))
    yield

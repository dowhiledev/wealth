from __future__ import annotations

from pathlib import Path

from sqlmodel import SQLModel, create_engine


def _sqlite_url(db_path: str) -> str:
    path = Path(db_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path}"


def get_engine(db_path: str):
    url = _sqlite_url(db_path)
    engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
    return engine


def init_db(db_path: str):
    """Create the SQLite database file and all known tables."""
    # Import models so metadata is populated
    from . import models  # noqa: F401

    engine = get_engine(db_path)
    # Connect once to ensure the file is created
    with engine.connect():
        pass
    SQLModel.metadata.create_all(engine)
    return engine

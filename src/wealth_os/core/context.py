from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Optional


DEFAULT_CONTEXT_FILE = os.getenv("WEALTH_CONTEXT_FILE") or str(
    Path.home() / ".wealth" / "context.json"
)


@dataclass
class Context:
    account_id: Optional[int] = None
    quote: Optional[str] = None
    providers: Optional[str] = None  # comma-separated provider order
    datasource: Optional[str] = None  # default datasource label for imports


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def get_context_path() -> Path:
    return Path(DEFAULT_CONTEXT_FILE).expanduser()


def load_context() -> Context:
    path = get_context_path()
    if not path.exists():
        return Context()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Context(**data)
    except Exception:
        return Context()


def save_context(ctx: Context) -> None:
    path = get_context_path()
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(ctx), f, indent=2)


def set_value(key: str, value: Any) -> Context:
    ctx = load_context()
    if not hasattr(ctx, key):
        raise KeyError(f"Unknown context key: {key}")
    setattr(ctx, key, value)
    save_context(ctx)
    return ctx


def unset_value(key: str) -> Context:
    ctx = load_context()
    if not hasattr(ctx, key):
        raise KeyError(f"Unknown context key: {key}")
    setattr(ctx, key, None)
    save_context(ctx)
    return ctx

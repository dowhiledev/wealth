from __future__ import annotations

from decimal import Decimal
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def fmt_decimal(x: Optional[Decimal], max_places: int = 8) -> str:
    if x is None:
        return ""
    s = format(x, "f")
    if "." in s:
        integer, frac = s.split(".", 1)
        frac = frac.rstrip("0")[:max_places]
        return integer if not frac else f"{integer}.{frac}"
    return s


def fmt_money(x: Optional[Decimal]) -> str:
    if x is None:
        return ""
    s = format(x, ".2f")
    return s


def colorize_pnl(x: Optional[Decimal]) -> Text:
    if x is None:
        return Text("-")
    style = "green" if x >= 0 else "red"
    return Text(fmt_money(x), style=style)


def success_panel(message: str) -> Panel:
    return Panel(Text(message, style="bold green"), border_style="green")


def info_panel(message: str) -> Panel:
    return Panel(Text(message, style="bold cyan"), border_style="cyan")

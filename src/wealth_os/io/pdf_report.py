from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from wealth_os.core.valuation import summarize_portfolio
from wealth_os.db.repo import session_scope


def generate_pdf_report(
    db_path: str,
    *,
    out_pdf: Path,
    as_of: datetime,
    quote: str = "USD",
    account_id: Optional[int] = None,
    allocation_img: Optional[Path] = None,
    value_img: Optional[Path] = None,
    pnl_img: Optional[Path] = None,
) -> Path:
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24,
    )
    story = []

    title = Paragraph("Wealth Report", styles["Title"])
    sub = Paragraph(f"As of {as_of.isoformat()} (quote {quote})", styles["Normal"])
    story += [title, sub, Spacer(1, 0.5 * cm)]

    # Portfolio summary table
    with session_scope(db_path) as s:
        positions, totals = summarize_portfolio(
            s, as_of=as_of, quote=quote, account_id=account_id
        )
    data = [["Asset", "Qty", "Price", "Value", "Cost Open", "Unrealized", "Realized"]]
    for p in positions:
        data.append(
            [
                p.asset,
                str(p.qty),
                str(p.price) if p.price is not None else "-",
                str(p.value) if p.value is not None else "-",
                str(p.cost_open) if p.cost_open is not None else "-",
                str(p.unrealized_pnl) if p.unrealized_pnl is not None else "-",
                str(p.realized_pnl),
            ]
        )
    data.append(
        [
            "Totals",
            "-",
            "-",
            str(totals["value"]),
            str(totals["cost_open"]),
            str(totals["unrealized"]),
            str(totals["realized"]),
        ]
    )

    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    story += [
        Paragraph("Portfolio Summary", styles["Heading2"]),
        table,
        Spacer(1, 0.5 * cm),
    ]

    # Charts
    if allocation_img and allocation_img.exists():
        story += [
            Paragraph("Allocation", styles["Heading2"]),
            Image(str(allocation_img), width=16 * cm, height=12 * cm),
            Spacer(1, 0.5 * cm),
        ]
    if value_img and value_img.exists():
        story += [
            Paragraph("Portfolio Value", styles["Heading2"]),
            Image(str(value_img), width=16 * cm, height=9 * cm),
            Spacer(1, 0.5 * cm),
        ]
    if pnl_img and pnl_img.exists():
        story += [
            Paragraph("Realized PnL", styles["Heading2"]),
            Image(str(pnl_img), width=16 * cm, height=9 * cm),
            Spacer(1, 0.5 * cm),
        ]

    doc.build(story)
    return out_pdf

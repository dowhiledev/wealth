from datetime import datetime, timedelta
from decimal import Decimal

from wealth_os.core.config import get_config
from wealth_os.core.valuation import summarize_portfolio
from wealth_os.db.repo import (
    session_scope,
    create_account,
    create_transaction,
    upsert_price,
)
from wealth_os.db.models import AccountType, TxSide


def test_fifo_valuation(tmp_db_path):
    cfg = get_config()
    t0 = datetime(2024, 1, 1, 12, 0, 0)
    with session_scope(cfg.db_path) as s:
        acc = create_account(s, name="Val", type_=AccountType.exchange)
        # Buys
        create_transaction(
            s,
            ts=t0,
            account_id=acc.id,
            asset_symbol="BTC",
            side=TxSide.buy,
            qty=Decimal("1"),
            total_quote=Decimal("10000"),
            quote_ccy="USD",
        )
        create_transaction(
            s,
            ts=t0 + timedelta(days=1),
            account_id=acc.id,
            asset_symbol="BTC",
            side=TxSide.buy,
            qty=Decimal("1"),
            total_quote=Decimal("20000"),
            quote_ccy="USD",
        )
        # Sell 1.5 at 30000
        create_transaction(
            s,
            ts=t0 + timedelta(days=2),
            account_id=acc.id,
            asset_symbol="BTC",
            side=TxSide.sell,
            qty=Decimal("1.5"),
            total_quote=Decimal("45000"),
            quote_ccy="USD",
        )
        # Price after
        upsert_price(
            s,
            asset_symbol="BTC",
            quote_ccy="USD",
            ts=t0 + timedelta(days=3),
            price=Decimal("30000"),
        )

    with session_scope(cfg.db_path) as s:
        positions, totals = summarize_portfolio(
            s, as_of=t0 + timedelta(days=4), quote="USD"
        )
    # Remaining qty = 0.5, value = 15000, open cost = 10000
    pos = {p.asset: p for p in positions}
    assert Decimal("0.5") == pos["BTC"].qty
    assert Decimal("15000") == pos["BTC"].value
    assert Decimal("10000") == pos["BTC"].cost_open
    assert Decimal("5000") == pos["BTC"].unrealized_pnl
    # Realized PnL = 45000 - (10000 + 0.5*20000) = 25000
    assert Decimal("25000") == pos["BTC"].realized_pnl

from datetime import datetime
from decimal import Decimal

from wealth_os.db.repo import (
    session_scope,
    create_account,
    list_accounts,
    create_transaction,
    list_transactions,
    update_transaction,
    delete_transaction,
)
from wealth_os.db.models import AccountType, TxSide
from wealth_os.core.config import get_config


def test_account_and_tx_crud(tmp_db_path):
    cfg = get_config()
    with session_scope(cfg.db_path) as s:
        acc = create_account(s, name="UnitTest", type_=AccountType.exchange)
        assert acc.id is not None
        acc_id = acc.id

    with session_scope(cfg.db_path) as s:
        accounts = list_accounts(s)
        assert any(a.name == "UnitTest" for a in accounts)

    with session_scope(cfg.db_path) as s:
        tx = create_transaction(
            s,
            ts=datetime(2024, 1, 1, 12, 0, 0),
            account_id=acc_id,
            asset_symbol="BTC",
            side=TxSide.buy,
            qty=Decimal("0.2"),
            price_quote=Decimal("30000"),
            total_quote=Decimal("6000"),
            quote_ccy="USD",
        )
        assert tx.id is not None

    with session_scope(cfg.db_path) as s:
        rows = list_transactions(s, account_id=acc_id)
        assert len(rows) == 1
        tx_id = rows[0].id

    with session_scope(cfg.db_path) as s:
        updated = update_transaction(s, tx_id, price_quote=Decimal("31000"))
        assert updated is not None
        assert str(updated.price_quote) == "31000"

    with session_scope(cfg.db_path) as s:
        ok = delete_transaction(s, tx_id)
        assert ok is True

    with session_scope(cfg.db_path) as s:
        rows = list_transactions(s, account_id=acc_id)
        assert len(rows) == 0

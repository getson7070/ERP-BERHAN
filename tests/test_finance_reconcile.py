import datetime as dt
from decimal import Decimal
import pytest

from erp.extensions import db
from erp.models import GLJournalEntry, GLJournalLine


def _auth_headers(user):
    return {}


@pytest.fixture
def finance_user(make_user_with_role):
    return make_user_with_role("finance")


def test_bank_statement_auto_match_simple(client, db_session, finance_user, resolve_org_id):
    org_id = resolve_org_id()
    headers = _auth_headers(finance_user)
    today = dt.date.today()

    entry = GLJournalEntry(
        org_id=org_id,
        journal_code="BANK",
        reference="CBE-TEST-1",
        currency="ETB",
        base_currency="ETB",
        fx_rate=Decimal("1"),
        document_date=today,
        posting_date=today,
        status="posted",
    )
    l1 = GLJournalLine(
        org_id=org_id,
        account_code="BANK-ETB-CBE-001",
        debit=Decimal("500"),
        credit=Decimal("0"),
        debit_base=Decimal("500"),
        credit_base=Decimal("0"),
    )
    l2 = GLJournalLine(
        org_id=org_id,
        account_code="REV-SALES",
        debit=Decimal("0"),
        credit=Decimal("500"),
        debit_base=Decimal("0"),
        credit_base=Decimal("500"),
    )
    entry.lines.extend([l1, l2])
    db.session.add(entry)
    db.session.commit()

    resp = client.post(
        "/api/finance/reconcile/bank-statements/import",
        json={
            "bank_account_code": "BANK-ETB-CBE-001",
            "currency": "ETB",
            "period_start": today.isoformat(),
            "period_end": today.isoformat(),
            "opening_balance": 0,
            "closing_balance": 500,
            "lines": [
                {
                    "tx_date": today.isoformat(),
                    "description": "Deposit",
                    "amount": 500,
                    "balance": 500,
                }
            ],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    stmt_id = resp.get_json()["statement_id"]

    resp = client.post(
        f"/api/finance/reconcile/bank-statements/{stmt_id}/auto-match",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["matched"] == 1

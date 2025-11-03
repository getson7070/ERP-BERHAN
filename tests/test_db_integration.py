from decimal import Decimal

from erp import create_app
from erp.extensions import db
from erp.models import Invoice


def test_invoice_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    with app.app_context():
        invoice = Invoice(org_id=1, number="INV-100", total=Decimal("99.99"))
        db.session.add(invoice)
        db.session.commit()
        found = Invoice.tenant_query(org_id=1).filter_by(number="INV-100").one()
        assert found.total == Decimal("99.99")



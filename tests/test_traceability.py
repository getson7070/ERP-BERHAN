from datetime import datetime, timedelta

from erp import create_app
from erp.extensions import db
from erp.inventory import Lot, assign_lot, check_expiry


def test_lot_assignment_and_expiry(tmp_path):
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/lot.db"
    with app.app_context():
        db.create_all()
        lot_number = assign_lot.apply(args=(1, 10)).get()
        lot = Lot.query.filter_by(lot_number=lot_number).first()
        assert lot is not None
        lot.expiry_date = datetime.utcnow() + timedelta(days=10)
        db.session.commit()
        assert check_expiry.apply().get() == 1

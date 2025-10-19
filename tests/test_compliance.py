from erp import create_app
from erp.extensions import db
from erp.compliance import ElectronicSignature


def test_signature_hash_chain(tmp_path):
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path}/sig.db"
    with app.app_context():
        db.create_all()
        first = ElectronicSignature(user_id=1, intent="approve")
        db.session.add(first)
        db.session.commit()
        second = ElectronicSignature(user_id=1, intent="review")
        db.session.add(second)
        db.session.commit()
        assert second.prev_hash == first.signature_hash



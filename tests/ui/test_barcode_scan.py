from erp import create_app
from erp.models import db, User


def setup_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        user = User(email="b@example.com", password="x", fs_uniquifier="u4")
        db.session.add(user)
        db.session.commit()
        return app, user.id


def login(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["logged_in"] = True


def test_verify_barcode_endpoint():
    app, user_id = setup_app()
    client = app.test_client()
    login(client, user_id)

    resp = client.post("/inventory/receive/verify", json={"barcode": "123"})
    assert resp.json["valid"] is True

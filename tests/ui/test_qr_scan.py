from erp import create_app
from erp.models import db, User


def setup_app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        WTF_CSRF_ENABLED=False,
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(email="c@example.com", password="x", fs_uniquifier="u5")
        db.session.add(user)
        db.session.commit()
        return app, user.id


def login(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["logged_in"] = True


def test_verify_qr_endpoint():
    app, user_id = setup_app()
    client = app.test_client()
    login(client, user_id)
    with client.session_transaction() as sess:
        sess["csrf_token"] = "testtoken"
        token = sess["csrf_token"]
    resp = client.post(
        "/inventory/receive/verify_qr",
        json={"qr_data": "ITEM123"},
        headers={"X-CSRFToken": token},
    )
    assert resp.json["valid"] is True

from erp import create_app
from erp.db import db, User, UserDashboard


def create_user(app):
    with app.app_context():
        user = User(email="u@example.com", password="x", fs_uniquifier="u1")
        db.session.add(user)
        db.session.commit()
        return user.id


def login(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["logged_in"] = True


def test_save_and_load_layout():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        user_id = create_user(app)
    client = app.test_client()
    login(client, user_id)

    resp = client.post("/dashboard/customize", json={"layout": "a"})
    assert resp.status_code == 200

    resp = client.get("/dashboard/customize")
    assert b"a" in resp.data
    with app.app_context():
        assert UserDashboard.query.filter_by(user_id=user_id).first().layout == "a"




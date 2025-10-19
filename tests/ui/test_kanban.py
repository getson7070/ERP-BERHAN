from erp import create_app
from erp.db import db, User


def setup_app():
    app = create_app()
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        user = User(email="k@example.com", password="x", fs_uniquifier="u3")
        db.session.add(user)
        db.session.commit()
        return app, user.id


def login(client, user_id):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["logged_in"] = True


def test_kanban_board_renders():
    app, user_id = setup_app()
    client = app.test_client()
    login(client, user_id)

    resp = client.get("/kanban/")
    assert b"To Do" in resp.data
    assert resp.status_code == 200




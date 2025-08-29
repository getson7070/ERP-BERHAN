from sqlalchemy import event
from erp import create_app
from erp.extensions import db
from erp.models import Inventory, Role, User
from erp import utils


def test_inventory_query_count(tmp_path, monkeypatch):
    db_path = tmp_path / 'test.db'
    if db_path.exists():
        db_path.unlink()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    app = create_app()
    with app.app_context():
        db.create_all()
        db.session.add(Inventory(org_id=1, name="Item", sku="I1", quantity=1))
        db.session.commit()
        counts = {'n': 0}

        @event.listens_for(db.engine, "before_cursor_execute")
        def count_queries(
            conn, cursor, statement, parameters, context, executemany
        ):
            counts['n'] += 1

        Inventory.query.all()
        event.remove(db.engine, "before_cursor_execute", count_queries)
    assert counts['n'] <= 1


def test_user_role_query_count(tmp_path, monkeypatch):
    user_db = tmp_path / 'user.db'
    if user_db.exists():
        user_db.unlink()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{user_db}")
    app = create_app()
    with app.app_context():
        db.create_all()
        role = Role(name="manager")
        user = User(
            email="u@example.com",
            password="hash",
            fs_uniquifier="abc",
            active=True,
        )
        user.roles.append(role)
        db.session.add_all([role, user])
        db.session.commit()
        counts = {'n': 0}

        @event.listens_for(db.engine, "before_cursor_execute")
        def count_queries(
            conn, cursor, statement, parameters, context, executemany
        ):
            counts['n'] += 1

        utils.load_users_with_roles()
        event.remove(db.engine, "before_cursor_execute", count_queries)
    assert counts['n'] <= 2

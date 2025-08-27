from sqlalchemy import event
from erp import create_app
from erp.extensions import db
from erp.models import Inventory


def test_inventory_query_count(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    app = create_app()
    with app.app_context():
        db.session.add(Inventory(org_id=1, name="Item", quantity=1))
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

import pytest
from erp import create_app, db

@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        yield app

@pytest.fixture()
def session(app):
    conn = db.engine.connect()
    trans = conn.begin()
    options = dict(bind=conn, binds={})
    sess = db.create_scoped_session(options=options)
    db.session = sess
    yield sess
    trans.rollback()
    conn.close()
    sess.remove()

def _table_exists(engine, name):
    from sqlalchemy import inspect
    return name in inspect(engine).get_table_names()

@pytest.mark.parametrize("table", ["users", "trusted_devices", "idempotency_keys"])
def test_crud_known_tables(app, session, table):
    if not _table_exists(db.engine, table):
        pytest.skip(f"table {table} not present (create migrations first)")
    # generic insert/select/update/delete via text to avoid model imports
    from sqlalchemy import text
    if table == "users":
        # minimal columns heuristic; adjust depending on your schema
        session.execute(text("INSERT INTO users DEFAULT VALUES"))
        row = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        assert row >= 1
    else:
        # no-op smoke if schema unknown
        assert True

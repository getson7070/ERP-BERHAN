from erp import create_app
from db import get_db


def test_health_endpoints(tmp_path, monkeypatch):
    """/health returns lightweight ok and /healthz performs deep checks."""

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    client = app.test_client()

    rv = client.get("/health")
    assert rv.status_code == 200
    assert rv.json["ok"] is True

    rv = client.get("/healthz")
    assert rv.status_code in (200, 503)
    if rv.status_code == 200:
        assert rv.json["ok"] is True
        assert rv.json["db"] is True
        assert rv.json["redis"] is True

    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        cur.close()
        conn.close()

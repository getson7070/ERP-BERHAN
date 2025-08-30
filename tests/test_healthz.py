from erp import create_app
from db import get_db


def test_health_endpoints(tmp_path, monkeypatch):
    """Both /health and /healthz should report dependencies as healthy."""

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_file))
    app = create_app()
    client = app.test_client()
    for path in ("/health", "/healthz"):
        rv = client.get(path)
        assert rv.status_code == 200
        assert rv.json["status"] == "ok"
        assert rv.json["db"] is True
        assert rv.json["redis"] is True
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1
        cur.close()
        conn.close()

from erp import create_app  # noqa: E402
from sqlalchemy import text  # noqa: E402
from db import get_db  # noqa: E402


def _setup_app(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "tenders.db"))
    monkeypatch.setenv("USE_FAKE_REDIS", "1")
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        conn = get_db()
        conn.execute(
            text(
                """
                CREATE TABLE tender_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE tenders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tender_type_id INTEGER,
                    description TEXT,
                    due_date TEXT,
                    workflow_state TEXT,
                    result TEXT,
                    awarded_to TEXT,
                    award_date TEXT,
                    username TEXT,
                    institution TEXT,
                    envelope_type TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO tender_types (type_name) VALUES ('A'), ('B')"
            )
        )
        conn.execute(
            text(
                "INSERT INTO tenders (tender_type_id, description, due_date, workflow_state, username, institution, envelope_type) VALUES "
                "(1, 'X', '2024-01-01', 'advert_registered', 'u1', 'Inst1', 'One Envelope'),"
                "(2, 'Y', '2024-02-01', 'advert_registered', 'u2', 'Inst2', 'Two Envelope')"
            )
        )
        conn.commit()
        conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess["logged_in"] = True
        sess["permissions"] = ["tenders_list"]
    return client


def test_export_csv(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/tenders/export.csv")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith("text/csv")
    assert b"X" in resp.data


def test_export_xlsx(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/tenders/export.xlsx")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"].startswith(
        "application/vnd.openxmlformats-officedocument"
    )


def test_sorting(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/tenders/list?sort=due_date&dir=desc")
    data = resp.get_json()
    assert data[0]["description"] == "Y"


def test_invalid_sort_defaults(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/tenders/list?sort=bogus&dir=desc")
    data = resp.get_json()
    assert data[0]["description"] == "Y"


def test_invalid_direction_defaults(tmp_path, monkeypatch):
    client = _setup_app(tmp_path, monkeypatch)
    resp = client.get("/tenders/list?sort=due_date&dir=sideways")
    data = resp.get_json()
    assert data[0]["description"] == "X"

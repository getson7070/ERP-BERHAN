import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from erp import create_app
from db import get_db


def test_row_level_isolation():
    app = create_app()
    with app.app_context():
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO inventory_items (org_id, name, quantity) VALUES (1,'A',1),(2,'B',1)")
        conn.commit(); cur.close(); conn.close()
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['org_id'] = 1
    rv = client.get('/inventory/')
    assert b'B' not in rv.data

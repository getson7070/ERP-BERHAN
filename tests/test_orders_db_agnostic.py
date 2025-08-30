from sqlalchemy import text
from flask import session
from erp import create_app
from db import get_db
from erp.routes import orders as orders_module


def test_orders_queries_parameterised():
    from pathlib import Path
    content = Path('erp/routes/orders.py').read_text()
    assert 'execute(text' in content
    assert '?' not in content


def test_orders_flow(tmp_path, monkeypatch):
    db_file = tmp_path / 'orders.db'
    monkeypatch.setenv('DATABASE_PATH', str(db_file))
    app = create_app()
    with app.app_context():
        conn = get_db()
        conn.execute(text('CREATE TABLE inventory (id INTEGER, item_code TEXT)'))
        conn.execute(text('CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, quantity INTEGER, customer TEXT, sales_rep TEXT, vat_exempt BOOLEAN, status TEXT)'))
        conn.execute(text("INSERT INTO inventory VALUES (1,'SKU1')"))
        conn.commit()
    with app.app_context():
        conn = get_db()
        conn.execute(text("INSERT INTO orders (item_id, quantity, customer, sales_rep, vat_exempt, status) VALUES (1,1,'Bob','alice',0,'pending')"))
        conn.commit()
        def fake_render(template, **ctx):
            return ctx
        orders_module.render_template = fake_render
        with app.test_request_context('/orders'):
            session['logged_in'] = True
            session['role'] = 'Sales Rep'
            session['permissions'] = ['view_orders']
            context = orders_module.orders()
            assert any(o[3] == 'Bob' for o in context['pending_orders'])

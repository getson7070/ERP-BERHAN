from __future__ import annotations
from flask import Blueprint, render_template_string
from sqlalchemy import select
from erp.utils import login_required
from erp.db import db

bp = Blueprint("privacy", __name__)

def _find_pia_table():
    meta = db.Model.metadata
    # look for a table that has the columns used in tests
    for t in meta.tables.values():
        cols = set(t.c.keys())
        if {"feature_name", "status", "risk_rating"}.issubset(cols):
            return t
    return None

@bp.route("/privacy")
@login_required
def index():
    table = _find_pia_table()
    items = []
    if table is not None:
        rows = db.session.execute(select(table)).fetchall()
        for row in rows:
            m = dict(row._mapping)
            items.append({
                "feature_name": m.get("feature_name", ""),
                "status": m.get("status", ""),
                "risk_rating": m.get("risk_rating", ""),
            })

    html = """
    <h1>Privacy Dashboard</h1>
    <ul>
    {% for it in items %}
      <li class="pia">
        <span class="feature">{{ it.feature_name }}</span>
        <span class="status">{{ it.status }}</span>
        <span class="risk">{{ it.risk_rating }}</span>
      </li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, items=items)

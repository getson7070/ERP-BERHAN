from __future__ import annotations
from flask import Blueprint, render_template_string
from sqlalchemy import select
from erp.utils import login_required
from erp.db import db

bp = Blueprint("privacy", __name__)

def _find_pia_table():
    meta = db.Model.metadata
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
        q = select(
            table.c.feature_name.label("feature_name"),
            table.c.status.label("status"),
            table.c.risk_rating.label("risk_rating"),
        )
        rows = db.session.execute(q).mappings().all()
        items = [dict(r) for r in rows]

    high_risk_count = sum(1 for it in items if str(it.get("risk_rating", "")).lower() == "high")
    open_dsr_count = sum(1 for it in items if "open" in str(it.get("status", "")).lower())

    html = """
    <h1>Privacy & Compliance Center</h1>
    <section class="summary">
      <div><strong>High-Risk Cases</strong>: {{ high_risk_count }}</div>
      <div><strong>Open DSRs</strong>: {{ open_dsr_count }}</div>
    </section>
<p class="contact">Contact: <a href="mailto:privacy@berhan.example">privacy@berhan.example</a></p>
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
    return render_template_string(html, items=items, high_risk_count=high_risk_count, open_dsr_count=open_dsr_count)




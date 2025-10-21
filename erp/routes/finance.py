# erp/routes/finance.py â€” fallback transactions UI compatible with templates
from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy import text
from ..extensions import db

bp = Blueprint("finance", __name__, url_prefix="/finance")

def _ensure_table():
    # Create table if it doesn't exist; safe for dev, prefer Alembic in prod
    ddl = """
    CREATE TABLE IF NOT EXISTS finance_transactions (
        id SERIAL PRIMARY KEY,
        org_id INTEGER,
        amount NUMERIC(12,2) NOT NULL,
        description TEXT,
        status VARCHAR(32) DEFAULT 'pending'
    )
    """
    db.session.execute(text(ddl))
    db.session.commit()

@bp.route("/")
def index():
    _ensure_table()
    org = session.get("org_id", 1)
    rows = db.session.execute(text("SELECT id, amount, description, status FROM finance_transactions WHERE org_id = :org OR :org = 1 ORDER BY id"), {"org": org}).mappings().all()
    return render_template("finance/index.html", transactions=rows)

@bp.route("/add", methods=["GET","POST"])
def add_transaction():
    _ensure_table()
    if request.method == "POST":
        org = session.get("org_id", 1)
        amount = request.form.get("amount", type=float)
        description = request.form.get("description", type=str)
        db.session.execute(text("INSERT INTO finance_transactions (org_id, amount, description, status) VALUES (:org, :amount, :desc, 'pending')"), {"org": org, "amount": amount, "desc": description})
        db.session.commit()
        return redirect(url_for("finance.index"))
    return render_template("finance/add.html")



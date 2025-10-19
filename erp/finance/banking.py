from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import login_required
from datetime import datetime
from decimal import Decimal
import csv, io

try:
    from erp.extensions import db
except Exception:
    db = None

banking_bp = Blueprint("banking", __name__, url_prefix="/finance/banking", template_folder="../templates")

if db:
    class BankAccount(db.Model):
        __tablename__ = "bank_accounts"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(128), unique=True, nullable=False)
        currency = db.Column(db.String(8), default="ETB")

    class BankStatement(db.Model):
        __tablename__ = "bank_statements"
        id = db.Column(db.Integer, primary_key=True)
        account_id = db.Column(db.Integer, db.ForeignKey("bank_accounts.id"), nullable=False)
        date = db.Column(db.Date, nullable=False)
        description = db.Column(db.String(255))
        amount = db.Column(db.Numeric(18,2), nullable=False)
        matched = db.Column(db.Boolean, default=False)

@banking_bp.route("/")
@login_required
def index():
    return render_template("finance/banking/index.html")

@banking_bp.route("/upload", methods=["GET","POST"])
@login_required
def upload():
    if request.method == "POST":
        if db is None:
            flash("DB not available", "danger")
            return redirect(url_for("banking.upload"))
        file = request.files.get("file")
        account = request.form.get("account","Main")
        # ensure account
        acct = db.session.query(BankAccount).filter_by(name=account).first()
        if not acct:
            acct = BankAccount(name=account)
            db.session.add(acct); db.session.flush()
        # parse CSV (date, description, amount)
        reader = csv.DictReader(io.StringIO(file.stream.read().decode("utf-8")))
        for row in reader:
            dt = datetime.fromisoformat(row["date"]).date()
            amt = Decimal(str(row["amount"]))
            db.session.add(BankStatement(account_id=acct.id, date=dt, description=row.get("description",""), amount=amt))
        db.session.commit()
        flash("Statement uploaded", "success")
        return redirect(url_for("banking.reconcile"))
    return render_template("finance/banking/upload.html")

@banking_bp.route("/reconcile", methods=["GET"])
@login_required
def reconcile():
    if db is None:
        txs = []
    else:
        txs = db.session.query(BankStatement).filter_by(matched=False).order_by(BankStatement.date.desc()).limit(200).all()
    return render_template("finance/banking/reconcile.html", txs=txs)

@banking_bp.route("/api/unmatched", methods=["GET"])
@login_required
def api_unmatched():
    if db is None:
        return jsonify([])
    txs = db.session.query(BankStatement).filter_by(matched=False).order_by(BankStatement.date.desc()).limit(500).all()
    return jsonify([{"id": t.id, "date": t.date.isoformat(), "description": t.description, "amount": float(t.amount)} for t in txs])



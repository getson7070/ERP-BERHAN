
from erp.extensions import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import date

class BankAccount(db.Model):
    __tablename__ = "bank_accounts"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(128), nullable=False)
    currency = db.Column(db.String(8), default="ETB")

class BankStatement(db.Model):
    __tablename__ = "bank_statements"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bank_account_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bank_accounts.id"))
    statement_date = db.Column(db.Date, default=date.today)

class StatementLine(db.Model):
    __tablename__ = "bank_statement_lines"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    statement_id = db.Column(UUID(as_uuid=True), db.ForeignKey("bank_statements.id"))
    amount = db.Column(db.Numeric(18,2), nullable=False)
    description = db.Column(db.String(255))
    matched_doc_type = db.Column(db.String(32))
    matched_doc_id = db.Column(UUID(as_uuid=True))



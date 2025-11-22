"""add finance gl, audit log, and reconciliation tables"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f5c2e7d9a4b"
down_revision = "7f0b1d2c3a4e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gl_journal_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("journal_code", sa.String(length=32), nullable=False, server_default="GENERAL"),
        sa.Column("reference", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
        sa.Column("fx_rate", sa.Numeric(14, 6), nullable=False, server_default="1.000000"),
        sa.Column("base_currency", sa.String(length=8), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=False),
        sa.Column("posting_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=True),
        sa.Column("posted_by_id", sa.Integer(), nullable=True),
        sa.Column("reversed_at", sa.DateTime(), nullable=True),
        sa.Column("reversed_by_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "gl_journal_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("journal_entry_id", sa.Integer(), nullable=False, index=True),
        sa.Column("account_code", sa.String(length=64), nullable=False, index=True),
        sa.Column("account_name", sa.String(length=255), nullable=True),
        sa.Column("debit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("debit_base", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("credit_base", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=32), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["journal_entry_id"], ["gl_journal_entries.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "finance_audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("event_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )

    op.create_table(
        "bank_statements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("bank_account_id", sa.Integer(), nullable=True, index=True),
        sa.Column("bank_account_code", sa.String(length=64), nullable=False, index=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="ETB"),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("opening_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("closing_balance", sa.Numeric(14, 2), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("external_reference", sa.String(length=128), nullable=True),
        sa.Column("statement_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),    )

    op.create_table(
        "bank_statement_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False, index=True),
        sa.Column("statement_id", sa.Integer(), nullable=False, index=True),
        sa.Column("tx_date", sa.Date(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("balance", sa.Numeric(14, 2), nullable=True),
        sa.Column("reference", sa.String(length=64), nullable=True),
        sa.Column("posted_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("finance_entry_id", sa.Integer(), nullable=True),
        sa.Column("matched", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column("matched_journal_entry_id", sa.Integer(), nullable=True, index=True),
        sa.Column("matched_at", sa.DateTime(), nullable=True),
        sa.Column("matched_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["statement_id"], ["bank_statements.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["matched_journal_entry_id"], ["gl_journal_entries.id"], ondelete="SET NULL"),
    )


def downgrade():
    op.drop_table("bank_statement_lines")
    op.drop_table("bank_statements")
    op.drop_table("finance_audit_log")
    op.drop_table("gl_journal_lines")
    op.drop_table("gl_journal_entries")

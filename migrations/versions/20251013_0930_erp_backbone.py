"""ERP backbone: finance, inventory, sales, procurement, hr
Revision ID: erp_backbone_20251013_0930
Revises: 
Create Date: 2025-10-13T09:30:01.241485
"""
from alembic import op
import sqlalchemy as sa
import uuid

# revision identifiers, used by Alembic.
revision = 'erp_backbone_20251013_0930'
down_revision = '0001_initial_core'  # <-- IMPORTANT: set this to your current head before running!
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('accounts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company', sa.String(length=128), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False, unique=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('is_group', sa.Boolean, default=False)
    )
    op.create_table('journal_entries',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('reference', sa.String(length=128)),
        sa.Column('remarks', sa.Text()),
        sa.Column('submitted', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime())
    )
    op.create_table('journal_lines',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('journal_entries.id'), nullable=False),
        sa.Column('account_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('party_type', sa.String(length=16)),
        sa.Column('party_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('debit', sa.Numeric(18,2), default=0),
        sa.Column('credit', sa.Numeric(18,2), default=0),
        sa.Column('description', sa.String(length=255))
    )
    op.create_table('customers',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=128), unique=True, nullable=False),
        sa.Column('currency', sa.String(length=8), default='ETB')
    )
    op.create_table('suppliers',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=128), unique=True, nullable=False),
        sa.Column('currency', sa.String(length=8), default='ETB')
    )
    op.create_table('invoices',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id')),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('total', sa.Numeric(18,2), nullable=False),
        sa.Column('status', sa.String(length=16), default='Draft')
    )
    op.create_table('receipts',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id')),
        sa.Column('amount', sa.Numeric(18,2), nullable=False),
        sa.Column('received_on', sa.Date(), nullable=False)
    )
    op.create_table('bills',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('suppliers.id')),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('total', sa.Numeric(18,2), nullable=False),
        sa.Column('status', sa.String(length=16), default='Draft')
    )
    op.create_table('payments',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('bill_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('bills.id')),
        sa.Column('amount', sa.Numeric(18,2), nullable=False),
        sa.Column('paid_on', sa.Date(), nullable=False)
    )

    # Inventory
    op.create_table('warehouses',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=128), unique=True, nullable=False)
    )
    op.create_table('items',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=64), unique=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('uom', sa.String(length=32), default='Unit'),
        sa.Column('valuation_method', sa.String(length=8), default='WAC')
    )
    op.create_table('lots',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('item_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('items.id'), nullable=False),
        sa.Column('number', sa.String(length=64)),
        sa.Column('expiry', sa.Date())
    )
    op.create_table('stock_ledger_entries',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('posting_time', sa.DateTime(), index=True),
        sa.Column('item_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('items.id'), nullable=False, index=True),
        sa.Column('warehouse_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('warehouses.id'), nullable=False, index=True),
        sa.Column('lot_id', sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey('lots.id'), nullable=True, index=True),
        sa.Column('qty', sa.Numeric(18,3), nullable=False),
        sa.Column('rate', sa.Numeric(18,4), nullable=False),
        sa.Column('value', sa.Numeric(18,2), nullable=False),
        sa.Column('voucher_type', sa.String(length=32)),
        sa.Column('voucher_id', sa.dialects.postgresql.UUID(as_uuid=True))
    )
    op.create_table('grn',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('posting_date', sa.Date(), nullable=False)
    )
    op.create_table('deliveries',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('posting_date', sa.Date(), nullable=False)
    )

    # Procurement & Sales
    op.create_table('purchase_orders',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('supplier_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=16), default='Draft')
    )
    op.create_table('sales_orders',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('posting_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=16), default='Draft')
    )

    # HR
    op.create_table('recruitment',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('position', sa.String(length=128), nullable=False),
        sa.Column('candidate', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), default='Applied'),
        sa.Column('created_at', sa.DateTime())
    )
    op.create_table('performance_reviews',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('employee_id', sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column('period', sa.String(length=32), nullable=False),
        sa.Column('score', sa.Numeric(5,2), default=0),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime())
    )

def downgrade():
    for t in ['performance_reviews','recruitment','sales_orders','purchase_orders','deliveries','grn','stock_ledger_entries','lots','items','warehouses','payments','bills','receipts','invoices','suppliers','customers','journal_lines','journal_entries','accounts']:
        op.drop_table(t)

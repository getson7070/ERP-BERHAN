"""Fix RLS policies to use current_setting('erp.org_id')::int."""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20250830_fix_rls_policies"
down_revision = "d4e5f6g7h8i"
branch_labels = None
depends_on = None

TENANT_TABLES = (
    "orders",
    "tenders",
    "inventory",
    "audit_logs",
    "finance_transactions",
    "inventory_items",
    "workflows",
    "crm_customers",
    "hr_employees",
    "procurement_suppliers",
    "manufacturing_jobs",
    "project_projects",
)

def upgrade():
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")
        op.execute(
            f"""
            CREATE POLICY org_rls ON {table}
            USING (org_id = current_setting('erp.org_id')::int)
            WITH CHECK (org_id = current_setting('erp.org_id')::int)
            """
        )

def downgrade():
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS org_rls ON {table}")

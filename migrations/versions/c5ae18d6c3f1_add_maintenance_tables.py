"""Add maintenance tables for assets and work orders."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "c5ae18d6c3f1"
down_revision = "9c2b4b3c6a5e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maintenance_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=True),
        sa.Column("manufacturer", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("salvage_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("useful_life_years", sa.Integer(), nullable=True),
        sa.Column("depreciation_method", sa.String(length=32), nullable=False, server_default="straight_line"),
        sa.Column("is_critical", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maintenance_assets_org", "maintenance_assets", ["org_id"])
    op.create_index("ix_maintenance_assets_code", "maintenance_assets", ["code"])
    op.create_index("ix_maintenance_assets_serial", "maintenance_assets", ["serial_number"])

    op.create_table(
        "maintenance_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("maintenance_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("schedule_type", sa.String(length=32), nullable=False, server_default="time"),
        sa.Column("interval_days", sa.Integer(), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("last_completed_date", sa.Date(), nullable=True),
        sa.Column("usage_metric", sa.String(length=64), nullable=True),
        sa.Column("usage_interval", sa.Integer(), nullable=True),
        sa.Column("last_usage_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_maintenance_schedules_org", "maintenance_schedules", ["org_id"])
    op.create_index("ix_maintenance_schedules_asset", "maintenance_schedules", ["asset_id"])

    op.create_table(
        "maintenance_work_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("maintenance_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("maintenance_schedules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("work_type", sa.String(length=32), nullable=False, server_default="corrective"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("requested_by_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_id", sa.Integer(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downtime_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downtime_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("downtime_minutes", sa.Integer(), nullable=True),
        sa.Column("labor_cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("material_cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("other_cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maintenance_work_orders_org", "maintenance_work_orders", ["org_id"])
    op.create_index("ix_maintenance_work_orders_asset", "maintenance_work_orders", ["asset_id"])
    op.create_index("ix_maintenance_work_orders_schedule", "maintenance_work_orders", ["schedule_id"])
    op.create_index("ix_maintenance_work_orders_status", "maintenance_work_orders", ["status"])

    op.create_table(
        "maintenance_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("from_status", sa.String(length=32), nullable=True),
        sa.Column("to_status", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_maintenance_events_org", "maintenance_events", ["org_id"])
    op.create_index("ix_maintenance_events_work_order", "maintenance_events", ["work_order_id"])
    op.create_index("ix_maintenance_events_type", "maintenance_events", ["event_type"])

    op.create_table(
        "maintenance_escalation_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("asset_category", sa.String(length=64), nullable=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("maintenance_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("min_priority", sa.String(length=32), nullable=False, server_default="normal"),
        sa.Column("downtime_threshold_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("notify_role", sa.String(length=64), nullable=True),
        sa.Column("notify_channel", sa.String(length=32), nullable=False, server_default="telegram"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_maintenance_escalation_rules_org", "maintenance_escalation_rules", ["org_id"])
    op.create_index("ix_maintenance_escalation_rules_asset", "maintenance_escalation_rules", ["asset_id"])

    op.create_table(
        "maintenance_escalation_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("rule_id", sa.Integer(), sa.ForeignKey("maintenance_escalation_rules.id", ondelete="SET NULL"), nullable=True),
        sa.Column("work_order_id", sa.Integer(), sa.ForeignKey("maintenance_work_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="triggered"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_maintenance_escalation_events_org", "maintenance_escalation_events", ["org_id"])
    op.create_index("ix_maintenance_escalation_events_work_order", "maintenance_escalation_events", ["work_order_id"])

    op.create_table(
        "maintenance_sensor_readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("maintenance_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sensor_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Numeric(14, 4), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_maintenance_sensor_readings_org", "maintenance_sensor_readings", ["org_id"])
    op.create_index("ix_maintenance_sensor_readings_asset", "maintenance_sensor_readings", ["asset_id"])
    op.create_index("ix_maintenance_sensor_readings_type", "maintenance_sensor_readings", ["sensor_type"])


def downgrade():
    op.drop_index("ix_maintenance_sensor_readings_type", table_name="maintenance_sensor_readings")
    op.drop_index("ix_maintenance_sensor_readings_asset", table_name="maintenance_sensor_readings")
    op.drop_index("ix_maintenance_sensor_readings_org", table_name="maintenance_sensor_readings")
    op.drop_table("maintenance_sensor_readings")

    op.drop_index("ix_maintenance_escalation_events_work_order", table_name="maintenance_escalation_events")
    op.drop_index("ix_maintenance_escalation_events_org", table_name="maintenance_escalation_events")
    op.drop_table("maintenance_escalation_events")

    op.drop_index("ix_maintenance_escalation_rules_asset", table_name="maintenance_escalation_rules")
    op.drop_index("ix_maintenance_escalation_rules_org", table_name="maintenance_escalation_rules")
    op.drop_table("maintenance_escalation_rules")

    op.drop_index("ix_maintenance_events_type", table_name="maintenance_events")
    op.drop_index("ix_maintenance_events_work_order", table_name="maintenance_events")
    op.drop_index("ix_maintenance_events_org", table_name="maintenance_events")
    op.drop_table("maintenance_events")

    op.drop_index("ix_maintenance_work_orders_status", table_name="maintenance_work_orders")
    op.drop_index("ix_maintenance_work_orders_schedule", table_name="maintenance_work_orders")
    op.drop_index("ix_maintenance_work_orders_asset", table_name="maintenance_work_orders")
    op.drop_index("ix_maintenance_work_orders_org", table_name="maintenance_work_orders")
    op.drop_table("maintenance_work_orders")

    op.drop_index("ix_maintenance_schedules_asset", table_name="maintenance_schedules")
    op.drop_index("ix_maintenance_schedules_org", table_name="maintenance_schedules")
    op.drop_table("maintenance_schedules")

    op.drop_index("ix_maintenance_assets_serial", table_name="maintenance_assets")
    op.drop_index("ix_maintenance_assets_code", table_name="maintenance_assets")
    op.drop_index("ix_maintenance_assets_org", table_name="maintenance_assets")
    op.drop_table("maintenance_assets")

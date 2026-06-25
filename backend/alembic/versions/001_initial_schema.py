"""001 — Initial GER2 CMMS schema
Revision ID: 001_initial
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # users
    op.create_table("users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="readonly"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("center_id", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # assets
    op.create_table("assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_code", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("manufacturer", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("serial_number", sa.String(100), unique=True, nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="operational"),
        sa.Column("center_id", sa.String(36), nullable=False),
        sa.Column("location_room", sa.String(100), nullable=False),
        sa.Column("acquisition_cost", sa.Float()),
        sa.Column("rul_score", sa.Float()),
        sa.Column("rul_computed_at", sa.String(30)),
        sa.Column("next_pm_date", sa.String(20)),
        sa.Column("dicom_ae_title", sa.String(64)),
        sa.Column("opcua_node_id", sa.String(255)),
        sa.Column("qr_code", sa.String(255)),
        sa.Column("rfid_tag", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # work_orders
    op.create_table("work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("wo_number", sa.String(30), unique=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="backlog"),
        sa.Column("wo_type", sa.String(30), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("center_id", sa.String(36), nullable=False),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_to_id", sa.String(36), sa.ForeignKey("users.id")),
        sa.Column("estimated_hours", sa.Float()),
        sa.Column("labor_cost", sa.Float()),
        sa.Column("parts_cost", sa.Float()),
        sa.Column("total_cost", sa.Float()),
        sa.Column("checklist", sa.JSON()),
        sa.Column("parts_used", sa.JSON()),
        sa.Column("ai_trigger_ref", sa.String(36)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # sensor_readings (TimescaleDB hypertable)
    op.create_table("sensor_readings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("timestamp_utc", sa.String(30), nullable=False),
        sa.Column("sensor_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("opcua_node_id", sa.String(255)),
        sa.Column("quality", sa.String(20)),
    )
    op.execute("SELECT create_hypertable('sensor_readings', 'timestamp_utc', if_not_exists => TRUE);")

    # compliance tables
    op.create_table("calibration_certs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("cert_type", sa.String(100), nullable=False),
        sa.Column("cert_number", sa.String(100), unique=True, nullable=False),
        sa.Column("issue_date", sa.String(20), nullable=False),
        sa.Column("expiry_date", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="valid"),
        sa.Column("pdf_url", sa.String(512)),
        sa.Column("digital_signature", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table("audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp_utc", sa.String(30), nullable=False),
        sa.Column("user_id", sa.String(36)),
        sa.Column("agent_id", sa.String(50)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("immutable", sa.Boolean(), server_default="true"),
    )
    op.create_table("cost_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("asset_id", sa.String(36), nullable=False),
        sa.Column("center_id", sa.String(36), nullable=False),
        sa.Column("cost_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(3), server_default="TND"),
        sa.Column("period_month", sa.String(7), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    for table in ["cost_records", "audit_logs", "calibration_certs", "sensor_readings", "work_orders", "assets", "users"]:
        op.drop_table(table)

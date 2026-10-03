"""Add append-only audit events.

Revision ID: 0006_audit_events
Revises: 0005_job_leases
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_audit_events"
down_revision: str | Sequence[str] | None = "0005_job_leases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("organization_id", sa.String(length=128), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_organization_id", "audit_events", ["organization_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_target_id", "audit_events", ["target_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_target_id", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_organization_id", table_name="audit_events")
    op.drop_table("audit_events")

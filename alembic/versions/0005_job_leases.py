"""Add worker leases and retry attempts.

Revision ID: 0005_job_leases
Revises: 0004_session_organization
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_job_leases"
down_revision: str | Sequence[str] | None = "0004_session_organization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.add_column(sa.Column("attempt", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("lease_owner", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index("ix_jobs_lease_expires_at", ["lease_expires_at"])


def downgrade() -> None:
    with op.batch_alter_table("jobs") as batch_op:
        batch_op.drop_index("ix_jobs_lease_expires_at")
        batch_op.drop_column("lease_expires_at")
        batch_op.drop_column("lease_owner")
        batch_op.drop_column("attempt")

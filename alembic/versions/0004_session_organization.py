"""Bind sessions to an organization.

Revision ID: 0004_session_organization
Revises: 0003_sessions
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_session_organization"
down_revision: str | Sequence[str] | None = "0003_sessions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.add_column(sa.Column("organization_id", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_sessions_organization_id", ["organization_id"])


def downgrade() -> None:
    with op.batch_alter_table("sessions") as batch_op:
        batch_op.drop_index("ix_sessions_organization_id")
        batch_op.drop_column("organization_id")

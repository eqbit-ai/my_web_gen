"""add user approval columns

Revision ID: a002
Revises: a001
Create Date: 2026-03-18
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a002'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _column_exists(connection, table_name, column_name, schema="public"):
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns"
            "  WHERE table_schema = :schema AND table_name = :table AND column_name = :col"
            ")"
        ),
        {"schema": schema, "table": table_name, "col": column_name},
    )
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    if not _column_exists(conn, "users", "is_approved"):
        op.add_column("users", sa.Column("is_approved", sa.Boolean(), server_default="false", nullable=False))

    if not _column_exists(conn, "users", "approved_at"):
        op.add_column("users", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))

    if not _column_exists(conn, "users", "approved_by"):
        op.add_column("users", sa.Column("approved_by", sa.Integer(), nullable=True))

    # Set existing active users as approved so they aren't locked out
    op.execute("UPDATE users SET is_approved = true WHERE is_active = true AND is_approved = false")


def downgrade() -> None:
    op.drop_column("users", "approved_by")
    op.drop_column("users", "approved_at")
    op.drop_column("users", "is_approved")

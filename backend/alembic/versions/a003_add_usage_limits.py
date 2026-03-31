"""add usage limits (edit_count, max_generations, max_edits)

Revision ID: a003
Revises: a002
Create Date: 2026-03-31
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a003'
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
    if not _column_exists(conn, "users", "edit_count"):
        op.add_column("users", sa.Column("edit_count", sa.Integer(), server_default="0", nullable=False))
    if not _column_exists(conn, "users", "max_generations"):
        op.add_column("users", sa.Column("max_generations", sa.Integer(), server_default="2", nullable=False))
    if not _column_exists(conn, "users", "max_edits"):
        op.add_column("users", sa.Column("max_edits", sa.Integer(), server_default="30", nullable=False))


def downgrade() -> None:
    op.drop_column("users", "max_edits")
    op.drop_column("users", "max_generations")
    op.drop_column("users", "edit_count")

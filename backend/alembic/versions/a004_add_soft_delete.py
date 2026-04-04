"""Add deleted_at column for soft-delete on projects and sites

Revision ID: a004
Revises: a003
Create Date: 2026-04-04
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a004"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add deleted_at to sites (public schema)
    op.add_column("sites", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

    # Add deleted_at to projects in all tenant schemas
    conn = op.get_bind()
    schemas = conn.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'")
    ).fetchall()
    for (schema_name,) in schemas:
        op.add_column(
            "projects",
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            schema=schema_name,
        )


def downgrade() -> None:
    op.drop_column("sites", "deleted_at")

    conn = op.get_bind()
    schemas = conn.execute(
        sa.text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%'")
    ).fetchall()
    for (schema_name,) in schemas:
        op.drop_column("projects", "deleted_at", schema=schema_name)

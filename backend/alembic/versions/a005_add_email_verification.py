"""add email verification columns

Revision ID: a005
Revises: a004
Create Date: 2026-04-07
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a005'
down_revision: str | None = 'a004'
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

    if not _column_exists(conn, "users", "email_verified"):
        op.add_column(
            "users",
            sa.Column("email_verified", sa.Boolean(), server_default="false", nullable=False),
        )

    if not _column_exists(conn, "users", "email_verification_token"):
        op.add_column(
            "users",
            sa.Column("email_verification_token", sa.String(), nullable=True),
        )
        op.create_index(
            "ix_users_email_verification_token",
            "users",
            ["email_verification_token"],
            unique=False,
        )

    if not _column_exists(conn, "users", "email_verification_sent_at"):
        op.add_column(
            "users",
            sa.Column("email_verification_sent_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Existing approved users are grandfathered in so they aren't locked out.
    # Guarded because is_approved may not yet exist in environments where the
    # earlier migration hasn't been applied.
    if _column_exists(conn, "users", "is_approved"):
        op.execute("UPDATE users SET email_verified = true WHERE is_approved = true")
    else:
        op.execute("UPDATE users SET email_verified = true")


def downgrade() -> None:
    op.drop_index("ix_users_email_verification_token", table_name="users")
    op.drop_column("users", "email_verification_sent_at")
    op.drop_column("users", "email_verification_token")
    op.drop_column("users", "email_verified")

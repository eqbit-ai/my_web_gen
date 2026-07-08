"""add edit_logs and edit_feedback tables

Revision ID: a006
Revises: a005
Create Date: 2026-04-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = 'a006'
down_revision: str | None = 'a005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(conn, name, schema="public"):
    return conn.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
            "WHERE table_schema=:s AND table_name=:t)"
        ),
        {"s": schema, "t": name},
    ).scalar()


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "edit_logs"):
        op.create_table(
            "edit_logs",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("project_id", UUID(as_uuid=True), nullable=True),
            sa.Column("session_id", sa.String(64), nullable=True),
            sa.Column("correlation_id", sa.String(64), nullable=True),
            sa.Column("prompt", sa.Text, nullable=False),
            sa.Column("edit_kind", sa.String(32), nullable=False),
            sa.Column("target_page", sa.String(64), nullable=True),
            sa.Column("category", sa.String(32), nullable=True),
            sa.Column("sections_edited", sa.String(255), nullable=True),
            sa.Column("full_rewrite", sa.Boolean, server_default=sa.text("false"), nullable=False),
            sa.Column("routing_confidence", sa.Float, nullable=True),
            sa.Column("success", sa.Boolean, server_default=sa.text("false"), nullable=False),
            sa.Column("error_kind", sa.String(64), nullable=True),
            sa.Column("duration_ms", sa.Integer, nullable=True),
            sa.Column("output_chars_delta", sa.Integer, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_edit_logs_user_id", "edit_logs", ["user_id"])
        op.create_index("ix_edit_logs_project_id", "edit_logs", ["project_id"])
        op.create_index("ix_edit_logs_session_id", "edit_logs", ["session_id"])
        op.create_index("ix_edit_logs_correlation_id", "edit_logs", ["correlation_id"])
        op.create_index("ix_edit_logs_edit_kind", "edit_logs", ["edit_kind"])
        op.create_index("ix_edit_logs_category", "edit_logs", ["category"])
        op.create_index("ix_edit_logs_success", "edit_logs", ["success"])
        op.create_index("ix_edit_logs_created_at", "edit_logs", ["created_at"])
        op.create_index("ix_edit_logs_category_success", "edit_logs", ["category", "success"])

    if not _table_exists(conn, "edit_feedback"):
        op.create_table(
            "edit_feedback",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("edit_log_id", UUID(as_uuid=True), sa.ForeignKey("edit_logs.id", ondelete="CASCADE"), nullable=False),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("rating", sa.String(8), nullable=False),
            sa.Column("comment", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_edit_feedback_edit_log_id", "edit_feedback", ["edit_log_id"])


def downgrade() -> None:
    op.drop_table("edit_feedback")
    op.drop_table("edit_logs")

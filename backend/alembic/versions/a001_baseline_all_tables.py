"""baseline: create all tables for fresh deployment

This migration creates every table defined in the SQLAlchemy models.
It is idempotent — each CREATE TABLE uses IF NOT EXISTS so it is safe
to run on databases that already have some or all tables created via
raw SQL or Base.metadata.create_all().

Existing incremental migrations (d95793ac1d51, b9e26e4ee549, 0ec1b4636ca4)
remain untouched.  This migration is inserted *before* the first one in the
chain so that a fresh database gets all tables first, then the incremental
migrations apply their ALTER/ADD operations (which gracefully no-op when the
columns already exist thanks to the IF NOT EXISTS guards here).

Revision ID: d8d84517254c
Revises:
Create Date: 2026-03-16 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "d8d84517254c"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(connection, table_name, schema="public"):
    """Check if a table already exists in the given schema."""
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.tables"
            "  WHERE table_schema = :schema AND table_name = :table"
            ")"
        ),
        {"schema": schema, "table": table_name},
    )
    return result.scalar()


def _column_exists(connection, table_name, column_name, schema="public"):
    """Check if a column already exists on a table."""
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.columns"
            "  WHERE table_schema = :schema"
            "    AND table_name = :table"
            "    AND column_name = :col"
            ")"
        ),
        {"schema": schema, "table": table_name, "col": column_name},
    )
    return result.scalar()


def _index_exists(connection, index_name):
    """Check if an index already exists."""
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM pg_indexes WHERE indexname = :name"
            ")"
        ),
        {"name": index_name},
    )
    return result.scalar()


def _constraint_exists(connection, constraint_name):
    """Check if a constraint already exists."""
    result = connection.execute(
        sa.text(
            "SELECT EXISTS ("
            "  SELECT 1 FROM information_schema.table_constraints"
            "  WHERE constraint_name = :name"
            ")"
        ),
        {"name": constraint_name},
    )
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # ── 1. users ──────────────────────────────────────────────────────────
    if not _table_exists(conn, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("company_name", sa.String(), nullable=True),
            sa.Column("license_number", sa.String(), nullable=True),
            sa.Column("mobile", sa.String(), nullable=True),
            sa.Column("db_schema", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
            sa.Column("generation_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("token_balance", sa.BigInteger(), server_default="1000000", nullable=False),
            sa.Column("tokens_used", sa.BigInteger(), server_default="0", nullable=False),
            sa.Column("licence_verified", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("licence_verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("licence_verified_by", sa.Integer(), nullable=True),
            sa.Column("force_password_reset", sa.Boolean(), server_default="false", nullable=False),
            sa.UniqueConstraint("email", name="uq_users_email"),
            sa.UniqueConstraint("license_number", name="uq_users_license_number"),
        )
        # Indexes
        op.create_index("ix_users_id", "users", ["id"])
        op.create_index("ix_users_email", "users", ["email"])
        op.create_index("ix_users_license_number", "users", ["license_number"])
    else:
        # Table exists — ensure all columns are present (for DBs created with older schema)
        for col_name, col_def in [
            ("is_admin", sa.Column("is_admin", sa.Boolean(), server_default="false", nullable=False)),
            ("is_active", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False)),
            ("last_login", sa.Column("last_login", sa.DateTime(timezone=True), nullable=True)),
            ("generation_count", sa.Column("generation_count", sa.Integer(), server_default="0", nullable=False)),
            ("token_balance", sa.Column("token_balance", sa.BigInteger(), server_default="1000000", nullable=False)),
            ("tokens_used", sa.Column("tokens_used", sa.BigInteger(), server_default="0", nullable=False)),
            ("licence_verified", sa.Column("licence_verified", sa.Boolean(), server_default="false", nullable=False)),
            ("licence_verified_at", sa.Column("licence_verified_at", sa.DateTime(timezone=True), nullable=True)),
            ("licence_verified_by", sa.Column("licence_verified_by", sa.Integer(), nullable=True)),
            ("force_password_reset", sa.Column("force_password_reset", sa.Boolean(), server_default="false", nullable=False)),
        ]:
            if not _column_exists(conn, "users", col_name):
                op.add_column("users", col_def)

    # ── 2. sites ──────────────────────────────────────────────────────────
    if not _table_exists(conn, "sites"):
        op.create_table(
            "sites",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("domain", sa.String(), nullable=True),
            sa.Column("cloudfront_distribution_id", sa.String(), nullable=True),
            sa.Column("cloudfront_domain", sa.String(), nullable=True),
            sa.Column("acm_certificate_arn", sa.String(), nullable=True),
            sa.Column("domain_status", sa.String(), nullable=True),
            sa.Column("dns_records", sa.JSON(), nullable=True),
            sa.Column("route53_zone_id", sa.String(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="draft"),
            sa.Column("is_multipage", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("page_count", sa.Integer(), server_default="1", nullable=False),
            sa.Column("deployed_url", sa.String(), nullable=True),
            sa.Column("cloudflare_project_name", sa.String(), nullable=True),
            sa.Column("session_id", sa.String(), nullable=True),
            sa.Column("deploy_error", sa.Text(), nullable=True),
            sa.Column("last_deployed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("domain", name="uq_sites_domain"),
        )
        op.create_index("ix_sites_user_id", "sites", ["user_id"])
        op.create_index("ix_sites_domain", "sites", ["domain"])
        op.create_index("ix_sites_session_id", "sites", ["session_id"])
    else:
        # Ensure columns added by later migrations exist
        for col_name, col_def in [
            ("cloudfront_distribution_id", sa.Column("cloudfront_distribution_id", sa.String(), nullable=True)),
            ("cloudfront_domain", sa.Column("cloudfront_domain", sa.String(), nullable=True)),
            ("acm_certificate_arn", sa.Column("acm_certificate_arn", sa.String(), nullable=True)),
            ("domain_status", sa.Column("domain_status", sa.String(), nullable=True)),
            ("dns_records", sa.Column("dns_records", sa.JSON(), nullable=True)),
            ("route53_zone_id", sa.Column("route53_zone_id", sa.String(), nullable=True)),
            ("is_multipage", sa.Column("is_multipage", sa.Boolean(), server_default="false", nullable=False)),
            ("page_count", sa.Column("page_count", sa.Integer(), server_default="1", nullable=False)),
            ("deployed_url", sa.Column("deployed_url", sa.String(), nullable=True)),
            ("cloudflare_project_name", sa.Column("cloudflare_project_name", sa.String(), nullable=True)),
            ("session_id", sa.Column("session_id", sa.String(), nullable=True)),
            ("deploy_error", sa.Column("deploy_error", sa.Text(), nullable=True)),
            ("last_deployed_at", sa.Column("last_deployed_at", sa.DateTime(timezone=True), nullable=True)),
        ]:
            if not _column_exists(conn, "sites", col_name):
                op.add_column("sites", col_def)

    # ── 3. domains ────────────────────────────────────────────────────────
    if not _table_exists(conn, "domains"):
        op.create_table(
            "domains",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("domain_name", sa.String(), nullable=False),
            sa.Column("tld", sa.String(), nullable=False),
            sa.Column("registrar", sa.String(), nullable=False, server_default="openprovider"),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("dns_status", sa.String(), nullable=False, server_default="healthy"),
            sa.Column("ssl_status", sa.String(), nullable=False, server_default="none"),
            sa.Column("ssl_expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("auto_renew", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("verification_status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("licence_number", sa.String(), nullable=True),
            sa.Column("verification_notes", sa.Text(), nullable=True),
            sa.Column("route53_zone_id", sa.String(), nullable=True),
            sa.Column("acm_certificate_arn", sa.String(), nullable=True),
            sa.Column("openprovider_domain_id", sa.Integer(), nullable=True),
            sa.Column("contact_handle", sa.String(), nullable=True),
            sa.Column("whois_privacy", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("transfer_locked", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("nameservers", postgresql.JSON(), nullable=True),
            sa.Column("transfer_requested_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("transfer_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("domain_name", name="uq_domains_domain_name"),
        )
        op.create_index("ix_domains_user_id", "domains", ["user_id"])
        op.create_index("ix_domains_domain_name", "domains", ["domain_name"])
        op.create_index("ix_domains_expires_at", "domains", ["expires_at"])

    # ── 4. audit_logs (explicit public schema) ────────────────────────────
    if not _table_exists(conn, "audit_logs", schema="public"):
        op.create_table(
            "audit_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("user_id", sa.String(), nullable=False),
            sa.Column("action", sa.String(100), nullable=False),
            sa.Column("resource_type", sa.String(100), nullable=False),
            sa.Column("resource_id", sa.String(255), nullable=True),
            sa.Column("details", postgresql.JSONB(), nullable=True),
            sa.Column("ip_address", sa.String(45), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            schema="public",
        )
        op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], schema="public")
        op.create_index("ix_audit_logs_action", "audit_logs", ["action"], schema="public")
        op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], schema="public")

    # ── 5. generation_logs ────────────────────────────────────────────────
    if not _table_exists(conn, "generation_logs"):
        op.create_table(
            "generation_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("job_id", sa.String(), nullable=True),
            sa.Column("session_id", sa.String(), nullable=True),
            sa.Column("prompt", sa.Text(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("stage_failed", sa.String(), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("html_size", sa.Integer(), nullable=True),
            sa.Column("tokens_consumed", sa.BigInteger(), server_default="0", nullable=False),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("is_multipage", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("page_count", sa.Integer(), server_default="1", nullable=False),
            sa.Column("performance_score", sa.Integer(), nullable=True),
            sa.Column("seo_score", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_generation_logs_user_id", "generation_logs", ["user_id"])

    # ── 6. password_reset_tokens ──────────────────────────────────────────
    if not _table_exists(conn, "password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("token", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("token", name="uq_password_reset_tokens_token"),
        )
        op.create_index("ix_password_reset_tokens_id", "password_reset_tokens", ["id"])
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"])
        op.create_index("ix_password_reset_tokens_token", "password_reset_tokens", ["token"])

    # ── 7. token_transactions ─────────────────────────────────────────────
    if not _table_exists(conn, "token_transactions"):
        op.create_table(
            "token_transactions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("type", sa.String(), nullable=False),
            sa.Column("amount", sa.BigInteger(), nullable=False),
            sa.Column("balance_after", sa.BigInteger(), nullable=False),
            sa.Column("reason", sa.String(), nullable=False),
            sa.Column("reference_id", sa.String(), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("created_by", sa.Integer(), nullable=True),
        )
        op.create_index("ix_token_transactions_user_id", "token_transactions", ["user_id"])
        op.create_index("ix_token_transactions_created_at", "token_transactions", ["created_at"])

    # ── 8. announcements ──────────────────────────────────────────────────
    if not _table_exists(conn, "announcements"):
        op.create_table(
            "announcements",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("type", sa.String(), nullable=False, server_default="info"),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    # ── 9. prompt_versions ────────────────────────────────────────────────
    if not _table_exists(conn, "prompt_versions"):
        op.create_table(
            "prompt_versions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("prompt_key", sa.String(), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("published_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("prompt_key", "version", name="uq_prompt_key_version"),
        )
        op.create_index("ix_prompt_versions_prompt_key", "prompt_versions", ["prompt_key"])

    # ── 10. login_events ──────────────────────────────────────────────────
    if not _table_exists(conn, "login_events"):
        op.create_table(
            "login_events",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("event_type", sa.String(), nullable=False),
            sa.Column("ip_address", sa.String(45), nullable=False),
            sa.Column("user_agent", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_login_events_user_id", "login_events", ["user_id"])
        op.create_index("ix_login_events_created_at", "login_events", ["created_at"])

    # ── 11. token_requests ────────────────────────────────────────────────
    if not _table_exists(conn, "token_requests"):
        op.create_table(
            "token_requests",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("amount", sa.BigInteger(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="pending"),
            sa.Column("admin_note", sa.Text(), nullable=True),
            sa.Column("reviewed_by", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_token_requests_user_id", "token_requests", ["user_id"])
        op.create_index("ix_token_requests_created_at", "token_requests", ["created_at"])

    # ── 12. projects (tenant table, but also needed in public for reference) ─
    if not _table_exists(conn, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String()),
            sa.Column("current_html", sa.Text()),
            sa.Column("current_css", sa.Text()),
            sa.Column("current_js", sa.Text()),
            sa.Column("metadata", sa.Text()),
            sa.Column("current_version", sa.Integer()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_projects_user_id", "projects", ["user_id"])

    # ── 13. project_versions ──────────────────────────────────────────────
    if not _table_exists(conn, "project_versions"):
        op.create_table(
            "project_versions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("project_id", sa.String(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
            sa.Column("version_number", sa.Integer(), nullable=False),
            sa.Column("html", sa.Text()),
            sa.Column("css", sa.Text()),
            sa.Column("js", sa.Text()),
            sa.Column("prompt", sa.Text()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("project_id", "version_number", name="uq_project_version"),
        )

    # ── 14. media ─────────────────────────────────────────────────────────
    if not _table_exists(conn, "media"):
        op.create_table(
            "media",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("project_id", sa.String(), nullable=True),
            sa.Column("filename", sa.String(), nullable=False),
            sa.Column("original_name", sa.String()),
            sa.Column("mime_type", sa.String()),
            sa.Column("size_bytes", sa.Integer()),
            sa.Column("width", sa.Integer(), nullable=True),
            sa.Column("height", sa.Integer(), nullable=True),
            sa.Column("url", sa.String(), nullable=False),
            sa.Column("category", sa.String()),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        )
        op.create_index("ix_media_user_id", "media", ["user_id"])
        op.create_index("ix_media_project_id", "media", ["project_id"])


def downgrade() -> None:
    """Drop all tables in reverse dependency order.

    WARNING: This destroys ALL data.  Only use on dev/test databases.
    """
    conn = op.get_bind()

    # Drop in reverse order (children first, parents last)
    for table, schema in [
        ("media", None),
        ("project_versions", None),
        ("projects", None),
        ("token_requests", None),
        ("login_events", None),
        ("prompt_versions", None),
        ("announcements", None),
        ("token_transactions", None),
        ("password_reset_tokens", None),
        ("generation_logs", None),
        ("domains", None),
        ("sites", None),
        ("audit_logs", "public"),
        ("users", None),
    ]:
        if _table_exists(conn, table, schema=schema or "public"):
            op.drop_table(table, schema=schema)

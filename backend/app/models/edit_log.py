"""
EditLog + EditFeedback models — capture every user-driven website edit so
we can build an eval set and improve prompt routing without 'training' the
LLM (we can't — it's frozen). The point is to learn from real prompts:
how users actually phrase requests, where the classifier mis-routes, and
which prompt categories produce the most thumbs-down.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class EditLog(Base):
    """One row per edit attempt (chat iterate, element edit, section edit)."""

    __tablename__ = "edit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    correlation_id = Column(String(64), nullable=True, index=True)

    # The actual prompt the user typed — full text, not truncated.
    prompt = Column(Text, nullable=False)
    # Endpoint that handled it: 'iterate' | 'element-edit' | 'section-edit' | 'cms-update'
    edit_kind = Column(String(32), nullable=False, index=True)
    # Page slug for multipage projects
    target_page = Column(String(64), nullable=True)

    # What the intent classifier decided (auto-tagged later if NULL).
    # Examples: 'rebrand', 'color_change', 'copy_edit', 'image_swap',
    # 'add_section', 'remove_section', 'layout_change', 'ambiguous'.
    category = Column(String(32), nullable=True, index=True)
    # Sections the router targeted (comma-joined for cheap querying).
    sections_edited = Column(String(255), nullable=True)
    # Whether the router took the full-page-rewrite escape hatch.
    full_rewrite = Column(Boolean, default=False, nullable=False)
    # Confidence score of the routing decision (0-1), if available.
    routing_confidence = Column(Float, nullable=True)

    # Outcome
    success = Column(Boolean, nullable=False, default=False, index=True)
    error_kind = Column(String(64), nullable=True)  # e.g. 'CircuitOpenError', 'TokenLimit', 'JSONParseError'
    duration_ms = Column(Integer, nullable=True)
    output_chars_delta = Column(Integer, nullable=True)  # |new_html| - |old_html|

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


Index("ix_edit_logs_category_success", EditLog.category, EditLog.success)


class EditFeedback(Base):
    """Thumbs up/down on a completed edit. Optional comment."""

    __tablename__ = "edit_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    edit_log_id = Column(UUID(as_uuid=True), ForeignKey("edit_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rating = Column(String(8), nullable=False)  # 'up' | 'down'
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

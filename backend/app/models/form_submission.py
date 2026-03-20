"""
FormSubmission model — stores contact form submissions from deployed websites.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.sql import func

from app.database import Base


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    fields = Column(JSON, nullable=False, default=dict)  # {name, email, phone, message, ...}
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    is_read = Column(Boolean, default=False, server_default="false", nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6-safe
    user_agent = Column(String(500), nullable=True)
    source_page = Column(String(255), nullable=True)  # e.g. "index.html", "contact.html"

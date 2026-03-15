"""
GenerationLog model — tracks every website generation attempt with timing,
token usage, quality scores, and failure diagnostics.
"""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class GenerationLog(Base):
    __tablename__ = "generation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    prompt = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="pending", server_default="pending")  # pending/processing/completed/failed
    stage_failed = Column(String, nullable=True)  # plan/html/js
    error_message = Column(Text, nullable=True)
    html_size = Column(Integer, nullable=True)
    tokens_consumed = Column(BigInteger, default=0, server_default="0", nullable=False)
    duration_ms = Column(Integer, nullable=True)
    is_multipage = Column(Boolean, default=False, server_default="false", nullable=False)
    page_count = Column(Integer, default=1, server_default="1", nullable=False)
    performance_score = Column(Integer, nullable=True)
    seo_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<GenerationLog {self.id} user={self.user_id} status={self.status}>"

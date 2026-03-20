"""
PageView model — tracks individual page views on deployed websites.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String(500), nullable=True, default="/")  # e.g. /index.html, /about.html
    referrer = Column(String(1000), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    country = Column(String(2), nullable=True)  # ISO country code (future)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

"""
Domain model — tracks registered domains, DNS/SSL health, and verification status.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Domain(Base):
    __tablename__ = "domains"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    domain_name = Column(String, nullable=False, unique=True, index=True)
    tld = Column(String, nullable=False)
    registrar = Column(String, nullable=False, default="openprovider", server_default="openprovider")
    status = Column(String, nullable=False, default="pending", server_default="pending")  # pending/active/expired/suspended
    dns_status = Column(String, nullable=False, default="healthy", server_default="healthy")  # healthy/degraded/error
    ssl_status = Column(String, nullable=False, default="none", server_default="none")  # active/expired/provisioning/none
    ssl_expires_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    auto_renew = Column(Boolean, default=True, server_default="true", nullable=False)
    verification_status = Column(String, nullable=False, default="pending", server_default="pending")  # pending/verified/rejected
    licence_number = Column(String, nullable=True)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Domain {self.domain_name} status={self.status}>"

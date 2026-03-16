"""
Domain model — tracks registered domains, DNS/SSL health, and verification status.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
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
    status = Column(String, nullable=False, default="pending", server_default="pending")
    dns_status = Column(String, nullable=False, default="healthy", server_default="healthy")
    ssl_status = Column(String, nullable=False, default="none", server_default="none")
    ssl_expires_at = Column(DateTime(timezone=True), nullable=True)
    registered_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    auto_renew = Column(Boolean, default=True, server_default="true", nullable=False)
    verification_status = Column(String, nullable=False, default="pending", server_default="pending")
    licence_number = Column(String, nullable=True)
    verification_notes = Column(Text, nullable=True)

    # Domain infrastructure fields (persist across site connections)
    route53_zone_id = Column(String, nullable=True)
    acm_certificate_arn = Column(String, nullable=True)
    openprovider_domain_id = Column(Integer, nullable=True)
    contact_handle = Column(String, nullable=True)
    whois_privacy = Column(Boolean, default=False, server_default="false", nullable=False)
    transfer_locked = Column(Boolean, default=True, server_default="true", nullable=False)
    nameservers = Column(JSON, nullable=True)

    # Transfer request (user → admin)
    transfer_requested_at = Column(DateTime(timezone=True), nullable=True)
    transfer_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Domain {self.domain_name} status={self.status}>"

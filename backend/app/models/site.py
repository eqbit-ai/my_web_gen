"""
Site model — represents a deployed (or draft) website belonging to a user.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, nullable=True, unique=True, index=True)
    cloudfront_distribution_id = Column(String, nullable=True)
    cloudfront_domain = Column(String, nullable=True)  # e.g. d1234.cloudfront.net
    acm_certificate_arn = Column(String, nullable=True)
    domain_status = Column(String, nullable=True)  # pending_validation / pending_deployment / active / failed
    dns_records = Column(JSON, nullable=True)  # JSON array of DNS records user needs to add
    route53_zone_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="draft", server_default="draft")  # draft/published/offline
    is_multipage = Column(Boolean, default=False, server_default="false", nullable=False)
    page_count = Column(Integer, default=1, server_default="1", nullable=False)
    deployed_url = Column(String, nullable=True)  # e.g. https://project-abc.pages.dev
    cloudflare_project_name = Column(String, nullable=True)  # CF Pages project name
    session_id = Column(String, nullable=True, index=True)  # Redis session used for deployment
    deploy_error = Column(Text, nullable=True)  # Last deployment error if any
    last_deployed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Site {self.id} name={self.name!r} status={self.status}>"

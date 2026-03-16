"""
TokenRequest model — user requests for more tokens, reviewed by admin.
"""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class TokenRequest(Base):
    __tablename__ = "token_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="pending", server_default="pending")  # pending/approved/rejected
    admin_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

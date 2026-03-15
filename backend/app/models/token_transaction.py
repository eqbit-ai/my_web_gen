"""
TokenTransaction model — immutable ledger for token grants, deductions, refunds, and expiries.
"""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database import Base


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # grant/deduction/expiry/refund
    amount = Column(BigInteger, nullable=False)  # positive for grants, negative for deductions
    balance_after = Column(BigInteger, nullable=False)
    reason = Column(String, nullable=False)
    reference_id = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<TokenTransaction {self.id} user={self.user_id} type={self.type} amount={self.amount}>"

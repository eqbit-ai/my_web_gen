from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    license_number = Column(String, unique=True, nullable=False, index=True)
    db_schema = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Admin panel fields
    is_admin = Column(Boolean, default=False, server_default="false", nullable=False)
    is_active = Column(Boolean, default=True, server_default="true", nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    generation_count = Column(Integer, default=0, server_default="0", nullable=False)

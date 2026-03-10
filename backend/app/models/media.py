"""
Media model — tracks uploaded files (images, logos, favicons, videos).
"""

import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Media(Base):
    __tablename__ = "media"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, nullable=False, index=True)
    project_id = Column(String, nullable=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, default="")
    mime_type = Column(String, default="")
    size_bytes = Column(Integer, default=0)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    url = Column(String, nullable=False)
    category = Column(String, default="image")  # image, logo, favicon, video
    created_at = Column(DateTime, server_default=func.now())

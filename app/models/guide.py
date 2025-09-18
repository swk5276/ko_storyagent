from sqlalchemy import Column, String, Text, DECIMAL, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class Guide(Base):
    __tablename__ = "guides"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    bio = Column(Text, nullable=True)
    rating = Column(DECIMAL(3, 2), default=0.00)
    total_reviews = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    created_at = Column(String(19), server_default=func.now())
    updated_at = Column(String(19), server_default=func.now(), onupdate=func.now())

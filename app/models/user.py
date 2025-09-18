from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kakao_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    nickname = Column(String(100), nullable=False)
    profile_image = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    chat_rooms_as_user = relationship("ChatRoom", foreign_keys="[ChatRoom.user_id]", back_populates="user")
    chat_rooms_as_guide = relationship("ChatRoom", foreign_keys="[ChatRoom.guide_id]", back_populates="guide")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

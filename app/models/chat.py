from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    guide_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    matching_request_id = Column(String(36), ForeignKey("matching_requests.id"), nullable=True)
    last_message = Column(Text, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="chat_rooms_as_user")
    guide = relationship("User", foreign_keys=[guide_id], back_populates="chat_rooms_as_guide")
    matching_request = relationship("MatchingRequest", backref="chat_room", uselist=False)
    messages = relationship("ChatMessage", back_populates="chat_room", cascade="all, delete-orphan")

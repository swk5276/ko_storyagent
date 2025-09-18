from sqlalchemy import Column, String, Text, Boolean, Enum, ForeignKey, Date, Time
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
import enum

class MatchingType(str, enum.Enum):
    online_chat = "online_chat"
    guide_tour = "guide_tour"
    home_visit = "home_visit"

class MatchingStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"

class MatchingRequest(Base):
    __tablename__ = "matching_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    guide_id = Column(String(36), ForeignKey("guides.id"), nullable=False)
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=True)
    matching_type = Column(Enum(MatchingType), nullable=False)
    status = Column(Enum(MatchingStatus), default=MatchingStatus.pending)
    requested_date = Column(Date, nullable=False)
    requested_time = Column(Time, nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(String(19), server_default=func.now())
    updated_at = Column(String(19), server_default=func.now(), onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chat_room_id = Column(String(36), ForeignKey("chat_rooms.id"), nullable=True)
    matching_request_id = Column(String(36), ForeignKey("matching_requests.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(String(19), server_default=func.now())
    
    # Relationships
    chat_room = relationship("ChatRoom", back_populates="messages")

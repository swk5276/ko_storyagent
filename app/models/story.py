from sqlalchemy import Column, String, Text, Integer, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class MediaType(str, enum.Enum):
    video = "video"
    image = "image"
    pdf = "pdf"
    audio = "audio"

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    guide_id = Column(String(36), ForeignKey("guides.id"), nullable=True)
    region_id1 = Column(String(50), nullable=True)  # 큰 지역 (수도권, 강원 등)
    region_id2 = Column(String(50), nullable=True)  # 세부 도시
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    media_type = Column(Enum(MediaType), nullable=False)
    media_url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(String(19), server_default=func.now())
    updated_at = Column(String(19), server_default=func.now(), onupdate=func.now())

class StoryLike(Base):
    __tablename__ = "story_likes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=False)
    created_at = Column(String(19), server_default=func.now())

class StoryComment(Base):
    __tablename__ = "story_comments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    parent_id = Column(String(36), ForeignKey("story_comments.id"), nullable=True)
    created_at = Column(String(19), server_default=func.now())
    updated_at = Column(String(19), server_default=func.now(), onupdate=func.now())

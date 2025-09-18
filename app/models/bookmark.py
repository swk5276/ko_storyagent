from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from app.core.database import Base
import uuid

class StoryBookmark(Base):
    __tablename__ = "story_bookmarks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    story_id = Column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(String(19), nullable=False)
    
    # 사용자당 스토리 중복 북마크 방지
    __table_args__ = (
        UniqueConstraint('user_id', 'story_id', name='unique_user_story_bookmark'),
    )

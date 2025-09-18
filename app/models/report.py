from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class StoryReport(Base):
    __tablename__ = "story_reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id"), nullable=False)
    reporter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

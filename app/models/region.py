from sqlalchemy import Column, String, Integer, DECIMAL
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Region(Base):
    __tablename__ = "regions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    region_name = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    district = Column(String(50), nullable=True)
    latitude = Column(DECIMAL(10, 8), nullable=True)
    longitude = Column(DECIMAL(11, 8), nullable=True)
    story_count = Column(Integer, default=0)
    created_at = Column(String(19), server_default=func.now())

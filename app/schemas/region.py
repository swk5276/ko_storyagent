from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RegionBase(BaseModel):
    region_name: str
    city: str
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RegionCreate(RegionBase):
    pass

class RegionResponse(RegionBase):
    id: str
    story_count: int
    created_at: datetime

class RegionListResponse(BaseModel):
    regions: List[RegionResponse]
    total: int

class RegionMapData(BaseModel):
    id: str
    city: str
    district: Optional[str] = None
    latitude: float
    longitude: float
    story_count: int
    popular_categories: List[str] = []

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MediaType(str, Enum):
    video = "video"
    image = "image"
    pdf = "pdf"
    audio = "audio"

class SortOrder(str, Enum):
    popular = "popular"
    latest = "latest"

# Story 관련 스키마
class StoryBase(BaseModel):
    title: str
    content: Optional[str] = None
    media_type: MediaType
    media_url: str
    thumbnail_url: Optional[str] = None
    category: Optional[str] = None
    region_id1: Optional[str] = None  # 큰 지역 (수도권, 강원 등)
    region_id2: Optional[str] = None  # 세부 도시

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

class StoryInDB(StoryBase):
    id: str
    user_id: str
    guide_id: Optional[str] = None
    view_count: int
    like_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class StoryResponse(StoryInDB):
    author_nickname: str
    author_profile_image: Optional[str] = None
    region_name: Optional[str] = None
    is_liked: bool = False
    is_bookmarked: bool = False
    comments_count: int = 0

class StoryListResponse(BaseModel):
    stories: List[StoryResponse]
    total: int
    page: int
    limit: int

# Comment 관련 스키마
class CommentCreate(BaseModel):
    content: str
    parent_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    story_id: str
    user_id: str
    user_nickname: str
    user_profile_image: Optional[str] = None
    content: str
    parent_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    replies: List['CommentResponse'] = []

CommentResponse.model_rebuild()

# Like 관련 스키마
class LikeToggleResponse(BaseModel):
    is_liked: bool
    like_count: int

# Report 관련 스키마
class StoryReportCreate(BaseModel):
    reason: str
    description: Optional[str] = None

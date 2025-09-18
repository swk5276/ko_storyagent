from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class MatchingType(str, Enum):
    online_chat = "online_chat"
    guide_tour = "guide_tour"
    home_visit = "home_visit"

class MatchingStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"
    cancelled = "cancelled"

# Guide 관련 스키마
class GuideCreate(BaseModel):
    bio: str

class GuideUpdate(BaseModel):
    bio: Optional[str] = None

class GuideResponse(BaseModel):
    id: str
    user_id: str
    bio: Optional[str] = None
    rating: float
    total_reviews: int
    is_approved: bool
    created_at: str  # 데이터베이스에서 문자열로 저장됨
    # User 정보
    nickname: str
    profile_image: Optional[str] = None

# Matching 관련 스키마
class MatchingRequestCreate(BaseModel):
    guide_id: str
    story_id: Optional[str] = None
    matching_type: MatchingType
    requested_date: date
    requested_time: Optional[time] = None
    message: Optional[str] = None

class MatchingRequestUpdate(BaseModel):
    status: MatchingStatus

class MatchingRequestResponse(BaseModel):
    id: str
    user_id: str
    guide_id: str
    story_id: Optional[str] = None
    matching_type: MatchingType
    status: MatchingStatus
    requested_date: date
    requested_time: Optional[time] = None
    message: Optional[str] = None
    created_at: str  # 데이터베이스에서 문자열로 저장됨
    updated_at: str  # 데이터베이스에서 문자열로 저장됨
    # 추가 정보
    user_nickname: str
    user_profile_image: Optional[str] = None
    guide_nickname: str
    guide_profile_image: Optional[str] = None
    story_title: Optional[str] = None
    chat_room_id: Optional[str] = None

class MatchingListResponse(BaseModel):
    requests: List[MatchingRequestResponse]
    total: int
    page: int
    limit: int

# Chat 관련 스키마
class ChatMessageCreate(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    chat_room_id: Optional[str] = None
    matching_request_id: str
    sender_id: str
    receiver_id: str
    message: str
    is_read: bool
    created_at: str  # 데이터베이스에서 문자열로 저장됨
    # 추가 정보
    sender_nickname: str
    sender_profile_image: Optional[str] = None

class ChatListResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int

# ChatRoom 관련 스키마
class ChatRoomResponse(BaseModel):
    id: str
    user_id: str
    guide_id: str
    matching_request_id: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    # 추가 정보
    user_nickname: str
    user_profile_image: Optional[str] = None
    guide_nickname: str
    guide_profile_image: Optional[str] = None
    unread_count: int = 0

class ChatRoomListResponse(BaseModel):
    rooms: List[ChatRoomResponse]
    total: int

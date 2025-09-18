from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[str] = None
    nickname: str
    profile_image: Optional[str] = None

class UserCreate(UserBase):
    kakao_id: str

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    profile_image: Optional[str] = None

class User(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class KakaoLoginRequest(BaseModel):
    access_token: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: User

class TokenRefresh(BaseModel):
    access_token: str
    token_type: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

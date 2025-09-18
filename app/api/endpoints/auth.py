from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.schemas.user import KakaoLoginRequest, Token, RefreshTokenRequest, TokenRefresh, User
from app.services.kakao_service import KakaoService
from app.models.user import User as UserModel, RefreshToken as RefreshTokenModel
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.database import get_db

router = APIRouter()

@router.post("/kakao/login", response_model=Token)
async def kakao_login(request: KakaoLoginRequest, db: Session = Depends(get_db)):
    """카카오 로그인"""
    print(f"카카오 로그인 요청 받음 - 액세스 토큰: {request.access_token[:20]}...")
    
    # 카카오 사용자 정보 가져오기
    kakao_user_info = await KakaoService.get_user_info(request.access_token)
    print(f"카카오 사용자 정보: {kakao_user_info}")
    if not kakao_user_info:
        raise HTTPException(status_code=401, detail="Invalid Kakao token")
    
    # 기존 사용자 확인 또는 새 사용자 생성
    user = db.query(UserModel).filter(UserModel.kakao_id == kakao_user_info["kakao_id"]).first()
    if not user:
        user = UserModel(
            kakao_id=kakao_user_info["kakao_id"],
            email=kakao_user_info.get("email"),
            nickname=kakao_user_info["nickname"],
            profile_image=kakao_user_info.get("profile_image")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # JWT 토큰 생성
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})
    
    # Refresh token을 DB에 저장
    expires_at = datetime.utcnow() + timedelta(days=7)
    refresh_token_obj = RefreshTokenModel(
        user_id=user.id,
        token=refresh_token,
        expires_at=expires_at
    )
    db.add(refresh_token_obj)
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": User(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            profile_image=user.profile_image,
            created_at=user.created_at
        )
    }

@router.post("/refresh", response_model=TokenRefresh)
async def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """토큰 갱신"""
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    # DB에서 refresh token 확인
    token_obj = db.query(RefreshTokenModel).filter(
        RefreshTokenModel.token == request.refresh_token
    ).first()
    
    if not token_obj or token_obj.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired or not found")
    
    # 새 액세스 토큰 발급
    new_access_token = create_access_token({"sub": token_obj.user_id})
    
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

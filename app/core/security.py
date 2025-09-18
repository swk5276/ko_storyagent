from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """현재 인증된 사용자 가져오기"""
    from app.models.user import User
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)), db: Session = Depends(get_db)):
    """선택적으로 현재 사용자 가져오기 (인증이 필수가 아닌 경우)"""
    from app.models.user import User
    
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user

async def get_current_user_ws(token: str, db: Session) -> Optional["User"]:
    """
    WebSocket용 사용자 인증 함수
    HTTPException 대신 None을 반환
    """
    from app.models.user import User
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        payload = decode_token(token)
        
        if not payload:
            logger.error("Failed to decode token")
            return None
            
        # 토큰 타입 확인
        if payload.get("type") != "access":
            logger.error(f"Invalid token type: {payload.get('type')}")
            return None
        
        # 만료 시간 확인
        exp = payload.get("exp")
        if exp:
            exp_datetime = datetime.fromtimestamp(exp)
            if exp_datetime < datetime.utcnow():
                logger.error(f"Token expired at {exp_datetime}")
                return None
        
        user_id = payload.get("sub")
        if not user_id:
            logger.error("No user_id in token")
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User not found: {user_id}")
            return None
            
        logger.info(f"WebSocket authentication successful for user: {user_id}")
        return user
        
    except Exception as e:
        logger.error(f"Error in WebSocket authentication: {e}")
        return None

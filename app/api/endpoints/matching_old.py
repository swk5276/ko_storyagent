from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.guide import Guide
from app.models.matching import MatchingRequest, ChatMessage
from app.models.story import Story
from app.schemas.matching import (
    GuideCreate, GuideUpdate, GuideResponse,
    MatchingRequestCreate, MatchingRequestUpdate, MatchingRequestResponse, MatchingListResponse,
    ChatMessageCreate, ChatMessageResponse, ChatListResponse, MatchingStatus
)
import uuid

router = APIRouter()

# Guide 관련 엔드포인트
@router.post("/guides/apply", response_model=GuideResponse)
async def apply_for_guide(
    guide_data: GuideCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """가이드 신청"""
    # 이미 가이드인지 확인
    existing_guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if existing_guide:
        raise HTTPException(status_code=400, detail="Already registered as guide")
    
    # 가이드 생성
    guide = Guide(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        bio=guide_data.bio,
        is_approved=True  # 테스트를 위해 자동 승인 (실제로는 False로 설정)
    )
    db.add(guide)
    db.commit()
    db.refresh(guide)
    
    return GuideResponse(
        id=guide.id,
        user_id=guide.user_id,
        bio=guide.bio,
        rating=float(guide.rating),
        total_reviews=guide.total_reviews,
        is_approved=guide.is_approved,
        created_at=datetime.fromisoformat(guide.created_at) if isinstance(guide.created_at, str) else guide.created_at,
        nickname=current_user.nickname,
        profile_image=current_user.profile_image
    )

@router.get("/guides/{guide_id}", response_model=GuideResponse)
async def get_guide(
    guide_id: str,
    db: Session = Depends(get_db)
):
    """가이드 정보 조회"""
    guide = db.query(Guide).filter(Guide.id == guide_id).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    
    user = db.query(User).filter(User.id == guide.user_id).first()
    
    return GuideResponse(
        id=guide.id,
        user_id=guide.user_id,
        bio=guide.bio,
        rating=float(guide.rating),
        total_reviews=guide.total_reviews,
        is_approved=guide.is_approved,
        created_at=datetime.fromisoformat(guide.created_at) if isinstance(guide.created_at, str) else guide.created_at,
        nickname=user.nickname if user else "Unknown",
        profile_image=user.profile_image if user else None
    )

# Matching 관련 엔드포인트
@router.post("/requests", response_model=MatchingRequestResponse)
async def create_matching_request(
    request_data: MatchingRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 생성"""
    # 가이드 확인
    guide = db.query(Guide).filter(Guide.id == request_data.guide_id).first()
    if not guide or not guide.is_approved:
        raise HTTPException(status_code=404, detail="Guide not found or not approved")
    
    # 자기 자신에게 요청 불가
    if guide.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot request matching with yourself")
    
    # 매칭 요청 생성
    matching_request = MatchingRequest(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **request_data.dict()
    )
    db.add(matching_request)
    db.commit()
    db.refresh(matching_request)
    
    # 가이드 사용자 정보
    guide_user = db.query(User).filter(User.id == guide.user_id).first()
    
    # 스토리 정보
    story = None
    if matching_request.story_id:
        story = db.query(Story).filter(Story.id == matching_request.story_id).first()
    
    return MatchingRequestResponse(
        id=matching_request.id,
        user_id=matching_request.user_id,
        guide_id=matching_request.guide_id,
        story_id=matching_request.story_id,
        matching_type=matching_request.matching_type,
        status=matching_request.status,
        requested_date=matching_request.requested_date,
        requested_time=matching_request.requested_time,
        message=matching_request.message,
        created_at=datetime.fromisoformat(matching_request.created_at) if isinstance(matching_request.created_at, str) else matching_request.created_at,
        updated_at=datetime.fromisoformat(matching_request.updated_at) if isinstance(matching_request.updated_at, str) else matching_request.updated_at,
        user_nickname=current_user.nickname,
        user_profile_image=current_user.profile_image,
        guide_nickname=guide_user.nickname if guide_user else "Unknown",
        guide_profile_image=guide_user.profile_image if guide_user else None,
        story_title=story.title if story else None
    )

@router.get("/requests", response_model=MatchingListResponse)
async def get_matching_requests(
    status: Optional[MatchingStatus] = None,
    as_guide: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 목록 조회"""
    query = db.query(MatchingRequest)
    
    if as_guide:
        # 가이드로서 받은 요청
        guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
        if not guide:
            raise HTTPException(status_code=403, detail="Not a guide")
        query = query.filter(MatchingRequest.guide_id == guide.id)
    else:
        # 사용자로서 보낸 요청
        query = query.filter(MatchingRequest.user_id == current_user.id)
    
    # 상태 필터
    if status:
        query = query.filter(MatchingRequest.status == status)
    
    # 정렬
    query = query.order_by(desc(MatchingRequest.created_at))
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    requests_db = query.offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    requests = []
    for req in requests_db:
        user = db.query(User).filter(User.id == req.user_id).first()
        guide = db.query(Guide).filter(Guide.id == req.guide_id).first()
        guide_user = db.query(User).filter(User.id == guide.user_id).first() if guide else None
        story = db.query(Story).filter(Story.id == req.story_id).first() if req.story_id else None
        
        requests.append(MatchingRequestResponse(
            id=req.id,
            user_id=req.user_id,
            guide_id=req.guide_id,
            story_id=req.story_id,
            matching_type=req.matching_type,
            status=req.status,
            requested_date=req.requested_date,
            requested_time=req.requested_time,
            message=req.message,
            created_at=datetime.fromisoformat(req.created_at) if isinstance(req.created_at, str) else req.created_at,
            updated_at=datetime.fromisoformat(req.updated_at) if isinstance(req.updated_at, str) else req.updated_at,
            user_nickname=user.nickname if user else "Unknown",
            user_profile_image=user.profile_image if user else None,
            guide_nickname=guide_user.nickname if guide_user else "Unknown",
            guide_profile_image=guide_user.profile_image if guide_user else None,
            story_title=story.title if story else None
        ))
    
    return MatchingListResponse(
        requests=requests,
        total=total,
        page=page,
        limit=limit
    )

@router.patch("/requests/{request_id}", response_model=MatchingRequestResponse)
async def update_matching_request(
    request_id: str,
    update_data: MatchingRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 상태 업데이트 (가이드만 가능)"""
    matching_request = db.query(MatchingRequest).filter(MatchingRequest.id == request_id).first()
    if not matching_request:
        raise HTTPException(status_code=404, detail="Matching request not found")
    
    # 가이드 확인
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if not guide or matching_request.guide_id != guide.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this request")
    
    # 상태 업데이트
    matching_request.status = update_data.status
    db.commit()
    db.refresh(matching_request)
    
    # 응답 데이터 구성
    user = db.query(User).filter(User.id == matching_request.user_id).first()
    story = db.query(Story).filter(Story.id == matching_request.story_id).first() if matching_request.story_id else None
    
    return MatchingRequestResponse(
        id=matching_request.id,
        user_id=matching_request.user_id,
        guide_id=matching_request.guide_id,
        story_id=matching_request.story_id,
        matching_type=matching_request.matching_type,
        status=matching_request.status,
        requested_date=matching_request.requested_date,
        requested_time=matching_request.requested_time,
        message=matching_request.message,
        created_at=datetime.fromisoformat(matching_request.created_at) if isinstance(matching_request.created_at, str) else matching_request.created_at,
        updated_at=datetime.fromisoformat(matching_request.updated_at) if isinstance(matching_request.updated_at, str) else matching_request.updated_at,
        user_nickname=user.nickname if user else "Unknown",
        user_profile_image=user.profile_image if user else None,
        guide_nickname=current_user.nickname,
        guide_profile_image=current_user.profile_image,
        story_title=story.title if story else None
    )

# Chat 관련 엔드포인트
@router.get("/requests/{request_id}/chat", response_model=ChatListResponse)
async def get_chat_messages(
    request_id: str,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 메시지 목록 조회"""
    # 매칭 요청 확인 및 권한 검증
    matching_request = db.query(MatchingRequest).filter(MatchingRequest.id == request_id).first()
    if not matching_request:
        raise HTTPException(status_code=404, detail="Matching request not found")
    
    # 가이드 정보 조회
    guide = db.query(Guide).filter(Guide.id == matching_request.guide_id).first()
    
    # 사용자 또는 가이드인지 확인
    if matching_request.user_id != current_user.id and guide.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view these messages")
    
    # 메시지 조회
    messages_db = db.query(ChatMessage).filter(
        ChatMessage.matching_request_id == request_id
    ).order_by(desc(ChatMessage.created_at)).limit(limit).all()
    
    # 읽음 처리
    unread_messages = [msg for msg in messages_db if msg.receiver_id == current_user.id and not msg.is_read]
    for msg in unread_messages:
        msg.is_read = True
    if unread_messages:
        db.commit()
    
    # 응답 데이터 구성
    messages = []
    for msg in reversed(messages_db):  # 시간순으로 정렬
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        messages.append(ChatMessageResponse(
            id=msg.id,
            matching_request_id=msg.matching_request_id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            message=msg.message,
            is_read=msg.is_read,
            created_at=datetime.fromisoformat(msg.created_at) if isinstance(msg.created_at, str) else msg.created_at,
            sender_nickname=sender.nickname if sender else "Unknown",
            sender_profile_image=sender.profile_image if sender else None
        ))
    
    return ChatListResponse(
        messages=messages,
        total=len(messages)
    )

@router.post("/requests/{request_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    request_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 메시지 전송"""
    # 매칭 요청 확인
    matching_request = db.query(MatchingRequest).filter(MatchingRequest.id == request_id).first()
    if not matching_request:
        raise HTTPException(status_code=404, detail="Matching request not found")
    
    # 가이드 정보 조회
    guide = db.query(Guide).filter(Guide.id == matching_request.guide_id).first()
    
    # 사용자 또는 가이드인지 확인
    if matching_request.user_id != current_user.id and guide.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to send messages")
    
    # 수신자 결정
    if current_user.id == matching_request.user_id:
        receiver_id = guide.user_id
    else:
        receiver_id = matching_request.user_id
    
    # 메시지 생성
    chat_message = ChatMessage(
        id=str(uuid.uuid4()),
        matching_request_id=request_id,
        sender_id=current_user.id,
        receiver_id=receiver_id,
        message=message_data.message
    )
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)
    
    return ChatMessageResponse(
        id=chat_message.id,
        matching_request_id=chat_message.matching_request_id,
        sender_id=chat_message.sender_id,
        receiver_id=chat_message.receiver_id,
        message=chat_message.message,
        is_read=chat_message.is_read,
        created_at=datetime.fromisoformat(chat_message.created_at) if isinstance(chat_message.created_at, str) else chat_message.created_at,
        sender_nickname=current_user.nickname,
        sender_profile_image=current_user.profile_image
    )

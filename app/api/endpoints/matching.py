from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.guide import Guide
from app.models.matching import MatchingRequest, ChatMessage
from app.models.chat import ChatRoom
from app.models.story import Story
from app.schemas.matching import (
    GuideCreate, GuideUpdate, GuideResponse,
    MatchingRequestCreate, MatchingRequestUpdate, MatchingRequestResponse, MatchingListResponse,
    ChatMessageCreate, ChatMessageResponse, ChatListResponse, MatchingStatus,
    ChatRoomResponse, ChatRoomListResponse
)
from app.services.matching_service import MatchingService

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
        created_at=guide.created_at,
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
        created_at=guide.created_at,
        nickname=user.nickname if user else "Unknown",
        profile_image=user.profile_image if user else None
    )

# Matching 관련 엔드포인트
@router.post("/requests", response_model=dict)
async def create_matching_request(
    request_data: MatchingRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 생성 및 채팅방 생성/반환"""
    matching_request = MatchingService.create_matching_request(
        db=db,
        user_id=current_user.id,
        request_data=request_data
    )
    
    # 가이드 사용자 정보
    guide = db.query(Guide).filter(Guide.id == matching_request.guide_id).first()
    guide_user = db.query(User).filter(User.id == guide.user_id).first()
    
    # 스토리 정보
    story = None
    if matching_request.story_id:
        story = db.query(Story).filter(Story.id == matching_request.story_id).first()
    
    # 매칭 요청이 즉시 수락되는 경우 (online_chat) - 제거
    # 모든 매칭 유형은 가이드의 승인이 필요함
    return {
        "matching_request": {
            "id": matching_request.id,
            "user_id": matching_request.user_id,
            "guide_id": matching_request.guide_id,
            "story_id": matching_request.story_id,
            "matching_type": matching_request.matching_type,
            "status": matching_request.status,
            "requested_date": matching_request.requested_date,
            "requested_time": matching_request.requested_time,
            "message": matching_request.message,
            "created_at": matching_request.created_at,
            "updated_at": matching_request.updated_at,
            "user_nickname": current_user.nickname,
            "user_profile_image": current_user.profile_image,
            "guide_nickname": guide_user.nickname if guide_user else "Unknown",
            "guide_profile_image": guide_user.profile_image if guide_user else None,
            "story_title": story.title if story else None
        },
        "chat_room_id": None
    }

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
    if as_guide:
        # 가이드로서 받은 요청
        guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
        if not guide:
            raise HTTPException(status_code=403, detail="Not a guide")
        requests = MatchingService.get_guide_matching_requests(db, guide.id, status)
    else:
        # 사용자로서 보낸 요청
        requests = MatchingService.get_user_matching_requests(db, current_user.id, status)
    
    # 페이지네이션
    total = len(requests)
    offset = (page - 1) * limit
    requests = requests[offset:offset + limit]
    
    # 응답 데이터 구성
    response_requests = []
    for req in requests:
        user = db.query(User).filter(User.id == req.user_id).first()
        guide = db.query(Guide).filter(Guide.id == req.guide_id).first()
        guide_user = db.query(User).filter(User.id == guide.user_id).first() if guide else None
        story = db.query(Story).filter(Story.id == req.story_id).first() if req.story_id else None
        
        # 채팅방 ID 찾기 (수락된 경우)
        chat_room_id = None
        if req.status == MatchingStatus.accepted:
            # 먼저 matching_request_id로 찾기
            chat_room = db.query(ChatRoom).filter(
                ChatRoom.matching_request_id == req.id
            ).first()
            
            # 못 찾으면 user_id와 guide_id로 찾기
            if not chat_room and guide:
                chat_room = db.query(ChatRoom).filter(
                    ChatRoom.user_id == req.user_id,
                    ChatRoom.guide_id == guide.user_id
                ).first()
            
            chat_room_id = chat_room.id if chat_room else None
        
        response_requests.append(MatchingRequestResponse(
            id=req.id,
            user_id=req.user_id,
            guide_id=req.guide_id,
            story_id=req.story_id,
            matching_type=req.matching_type,
            status=req.status,
            requested_date=req.requested_date,
            requested_time=req.requested_time,
            message=req.message,
            created_at=req.created_at,
            updated_at=req.updated_at,
            user_nickname=user.nickname if user else "Unknown",
            user_profile_image=user.profile_image if user else None,
            guide_nickname=guide_user.nickname if guide_user else "Unknown",
            guide_profile_image=guide_user.profile_image if guide_user else None,
            story_title=story.title if story else None,
            chat_room_id=chat_room_id
        ))
    
    return MatchingListResponse(
        requests=response_requests,
        total=total,
        page=page,
        limit=limit
    )

@router.patch("/requests/{request_id}", response_model=dict)
async def update_matching_request(
    request_id: str,
    update_data: MatchingRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 상태 업데이트 (가이드만 가능)"""
    import logging
    logger = logging.getLogger(__name__)
    
    # 가이드 확인
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if not guide:
        raise HTTPException(status_code=403, detail="Not a guide")
    
    logger.info(f"Guide {guide.id} (user: {current_user.id}) updating matching request {request_id} to {update_data.status}")
    
    matching_request = MatchingService.update_matching_status(
        db=db,
        matching_id=request_id,
        guide_id=guide.id,
        new_status=update_data.status
    )
    
    # 응답 데이터 구성
    user = db.query(User).filter(User.id == matching_request.user_id).first()
    story = db.query(Story).filter(Story.id == matching_request.story_id).first() if matching_request.story_id else None
    
    response = {
        "matching_request": {
            "id": matching_request.id,
            "user_id": matching_request.user_id,
            "guide_id": matching_request.guide_id,
            "story_id": matching_request.story_id,
            "matching_type": matching_request.matching_type,
            "status": matching_request.status,
            "requested_date": matching_request.requested_date,
            "requested_time": matching_request.requested_time,
            "message": matching_request.message,
            "created_at": matching_request.created_at,
            "updated_at": matching_request.updated_at,
            "user_nickname": user.nickname if user else "Unknown",
            "user_profile_image": user.profile_image if user else None,
            "guide_nickname": current_user.nickname,
            "guide_profile_image": current_user.profile_image,
            "story_title": story.title if story else None
        }
    }
    
    # 수락된 경우 채팅방 ID 포함
    if update_data.status == MatchingStatus.accepted:
        # 방금 생성된 채팅방 찾기
        chat_room = db.query(ChatRoom).filter(
            ChatRoom.matching_request_id == matching_request.id
        ).first()
        
        # matching_request_id로 못 찾으면 user_id와 guide_id로 찾기
        if not chat_room:
            chat_room = db.query(ChatRoom).filter(
                ChatRoom.user_id == matching_request.user_id,
                ChatRoom.guide_id == current_user.id
            ).first()
        
        if chat_room:
            logger.info(f"Found chat room {chat_room.id} for matching request {matching_request.id}")
        else:
            logger.warning(f"No chat room found for matching request {matching_request.id}")
            
        response["chat_room_id"] = chat_room.id if chat_room else None
    else:
        response["chat_room_id"] = None
    
    return response

@router.delete("/requests/{request_id}")
async def delete_matching_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """매칭 요청 삭제 (매칭 끊기)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Delete matching request called: request_id={request_id}, user_id={current_user.id}")
    
    try:
        success = MatchingService.delete_matching_request(
            db=db,
            matching_id=request_id,
            user_id=current_user.id
        )
        
        logger.info(f"Delete matching request result: success={success}")
        
        if success:
            return {"message": "Matching request has been cancelled"}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to cancel matching request"
            )
    except Exception as e:
        logger.error(f"Error deleting matching request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting matching request: {str(e)}"
        )

# ChatRoom 관련 엔드포인트
@router.get("/chat-rooms", response_model=ChatRoomListResponse)
async def get_chat_rooms(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방 목록 조회"""
    rooms = MatchingService.get_user_chat_rooms(db, current_user.id)
    
    response_rooms = []
    for room in rooms:
        # 사용자 정보
        user = db.query(User).filter(User.id == room.user_id).first()
        guide = db.query(User).filter(User.id == room.guide_id).first()
        
        # 읽지 않은 메시지 개수
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room.id,
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.is_read == False
        ).count()
        
        response_rooms.append(ChatRoomResponse(
            id=room.id,
            user_id=room.user_id,
            guide_id=room.guide_id,
            matching_request_id=room.matching_request_id,
            last_message=room.last_message,
            last_message_at=room.last_message_at,
            is_active=room.is_active,
            created_at=room.created_at,
            user_nickname=user.nickname if user else "Unknown",
            user_profile_image=user.profile_image if user else None,
            guide_nickname=guide.nickname if guide else "Unknown",
            guide_profile_image=guide.profile_image if guide else None,
            unread_count=unread_count
        ))
    
    return ChatRoomListResponse(
        rooms=response_rooms,
        total=len(response_rooms)
    )

@router.get("/chat-rooms/{room_id}", response_model=ChatRoomResponse)
async def get_chat_room(
    room_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅방 정보 조회"""
    room = MatchingService.get_chat_room(db, room_id, current_user.id)
    
    # 사용자 정보
    user = db.query(User).filter(User.id == room.user_id).first()
    guide = db.query(User).filter(User.id == room.guide_id).first()
    
    # 읽지 않은 메시지 개수
    unread_count = db.query(ChatMessage).filter(
        ChatMessage.chat_room_id == room.id,
        ChatMessage.receiver_id == current_user.id,
        ChatMessage.is_read == False
    ).count()
    
    return ChatRoomResponse(
        id=room.id,
        user_id=room.user_id,
        guide_id=room.guide_id,
        matching_request_id=room.matching_request_id,
        last_message=room.last_message,
        last_message_at=room.last_message_at,
        is_active=room.is_active,
        created_at=room.created_at,
        user_nickname=user.nickname if user else "Unknown",
        user_profile_image=user.profile_image if user else None,
        guide_nickname=guide.nickname if guide else "Unknown",
        guide_profile_image=guide.profile_image if guide else None,
        unread_count=unread_count
    )

@router.get("/chat-rooms/{room_id}/messages", response_model=ChatListResponse)
async def get_chat_messages(
    room_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 메시지 목록 조회"""
    messages = MatchingService.get_chat_messages(db, room_id, current_user.id, limit, offset)
    
    response_messages = []
    for msg in messages:
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        response_messages.append(ChatMessageResponse(
            id=msg.id,
            chat_room_id=msg.chat_room_id,
            matching_request_id=msg.matching_request_id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            message=msg.message,
            is_read=msg.is_read,
            created_at=msg.created_at,
            sender_nickname=sender.nickname if sender else "Unknown",
            sender_profile_image=sender.profile_image if sender else None
        ))
    
    return ChatListResponse(
        messages=response_messages,
        total=len(response_messages)
    )

@router.post("/chat-rooms/{room_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    room_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """채팅 메시지 전송"""
    # 채팅방 확인
    chat_room = db.query(ChatRoom).filter(
        ChatRoom.id == room_id,
        ChatRoom.is_active == True
    ).first()
    
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")
    
    # 권한 확인
    if current_user.id not in [chat_room.user_id, chat_room.guide_id]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # 메시지 저장
    message = MatchingService.send_message(
        db=db,
        room_id=room_id,
        sender_id=current_user.id,
        message=message_data.message
    )
    
    # WebSocket으로 실시간 전송
    from app.websocket.chat_websocket import manager
    
    # 수신자 ID 결정
    receiver_id = chat_room.guide_id if current_user.id == chat_room.user_id else chat_room.user_id
    
    # WebSocket 메시지 데이터 구성
    ws_message = {
        "type": "message",
        "room_id": room_id,
        "data": {
            "id": message.id,
            "chat_room_id": message.chat_room_id,
            "matching_request_id": message.matching_request_id,
            "sender_id": message.sender_id,
            "receiver_id": message.receiver_id,
            "message": message.message,
            "is_read": message.is_read,
            "created_at": message.created_at,
            "sender_nickname": current_user.nickname,
            "sender_profile_image": current_user.profile_image
        }
    }
    
    # 수신자에게만 전송 (발신자는 이미 화면에 표시됨)
    await manager.send_personal_message(ws_message, receiver_id)
    
    return ChatMessageResponse(
        id=message.id,
        chat_room_id=message.chat_room_id,
        matching_request_id=message.matching_request_id,
        sender_id=message.sender_id,
        receiver_id=message.receiver_id,
        message=message.message,
        is_read=message.is_read,
        created_at=message.created_at,
        sender_nickname=current_user.nickname,
        sender_profile_image=current_user.profile_image
    )

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Optional, List
from datetime import datetime
import uuid

from app.models.matching import MatchingRequest, MatchingStatus, ChatMessage
from app.models.chat import ChatRoom
from app.models.user import User
from app.models.guide import Guide
from app.schemas.matching import MatchingRequestCreate, MatchingRequestUpdate


class MatchingService:
    @staticmethod
    def create_matching_request(
        db: Session,
        user_id: str,
        request_data: MatchingRequestCreate
    ) -> MatchingRequest:
        """매칭 요청 생성"""
        # 가이드 존재 확인
        guide = db.query(Guide).filter(Guide.id == request_data.guide_id).first()
        if not guide:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guide not found"
            )
        
        # 가이드가 승인되었는지 확인
        if not guide.is_approved:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guide is not approved yet"
            )
        
        # 이미 진행 중인 매칭이 있는지 확인
        existing_request = db.query(MatchingRequest).filter(
            MatchingRequest.user_id == user_id,
            MatchingRequest.guide_id == request_data.guide_id,
            MatchingRequest.status.in_([MatchingStatus.pending, MatchingStatus.accepted])
        ).first()
        
        if existing_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already has an active matching request with this guide"
            )
        
        # 매칭 요청 생성
        matching_request = MatchingRequest(
            user_id=user_id,
            **request_data.dict()
        )
        db.add(matching_request)
        db.commit()
        db.refresh(matching_request)
        
        return matching_request
    
    @staticmethod
    def get_user_matching_requests(
        db: Session,
        user_id: str,
        status: Optional[MatchingStatus] = None
    ) -> List[MatchingRequest]:
        """사용자의 매칭 요청 목록 조회"""
        query = db.query(MatchingRequest).filter(MatchingRequest.user_id == user_id)
        
        if status:
            query = query.filter(MatchingRequest.status == status)
        
        return query.order_by(MatchingRequest.created_at.desc()).all()
    
    @staticmethod
    def get_guide_matching_requests(
        db: Session,
        guide_id: str,
        status: Optional[MatchingStatus] = None
    ) -> List[MatchingRequest]:
        """가이드의 매칭 요청 목록 조회"""
        query = db.query(MatchingRequest).filter(MatchingRequest.guide_id == guide_id)
        
        if status:
            query = query.filter(MatchingRequest.status == status)
        
        return query.order_by(MatchingRequest.created_at.desc()).all()
    
    @staticmethod
    def update_matching_status(
        db: Session,
        matching_id: str,
        guide_id: str,
        new_status: MatchingStatus
    ) -> MatchingRequest:
        """매칭 요청 상태 업데이트 (가이드만 가능)"""
        matching_request = db.query(MatchingRequest).filter(
            MatchingRequest.id == matching_id,
            MatchingRequest.guide_id == guide_id
        ).first()
        
        if not matching_request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matching request not found"
            )
        
        # 상태 변경 가능 여부 확인
        if matching_request.status != MatchingStatus.pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {matching_request.status} to {new_status}"
            )
        
        matching_request.status = new_status
        
        # 수락된 경우 채팅방 생성
        if new_status == MatchingStatus.accepted:
            # Guide 테이블에서 가이드의 user_id를 가져옴
            guide = db.query(Guide).filter(Guide.id == guide_id).first()
            if guide:
                chat_room = MatchingService.create_or_get_chat_room(
                    db,
                    matching_request.user_id,
                    guide.user_id,  # Guide의 user_id를 사용
                    matching_request.id
                )
        
        db.commit()
        db.refresh(matching_request)
        
        return matching_request
    
    @staticmethod
    def create_or_get_chat_room(
        db: Session,
        user_id: str,
        guide_id: str,
        matching_request_id: Optional[str] = None
    ) -> ChatRoom:
        """채팅방 생성 또는 기존 채팅방 반환"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating/getting chat room: user_id={user_id}, guide_id={guide_id}, matching_request_id={matching_request_id}")
        
        # 기존 채팅방 확인
        existing_room = db.query(ChatRoom).filter(
            ChatRoom.user_id == user_id,
            ChatRoom.guide_id == guide_id,
            ChatRoom.is_active == True
        ).first()
        
        if existing_room:
            logger.info(f"Found existing chat room: {existing_room.id}")
            # 매칭 요청 ID 업데이트 (필요한 경우)
            if matching_request_id and not existing_room.matching_request_id:
                existing_room.matching_request_id = matching_request_id
                db.commit()
                db.refresh(existing_room)
            return existing_room
        
        # 새 채팅방 생성
        chat_room = ChatRoom(
            user_id=user_id,
            guide_id=guide_id,
            matching_request_id=matching_request_id
        )
        db.add(chat_room)
        db.commit()
        db.refresh(chat_room)
        
        logger.info(f"Created new chat room: {chat_room.id}")
        
        return chat_room
    
    @staticmethod
    def get_chat_room(
        db: Session,
        room_id: str,
        user_id: str
    ) -> ChatRoom:
        """채팅방 조회"""
        chat_room = db.query(ChatRoom).filter(
            ChatRoom.id == room_id,
            ChatRoom.is_active == True
        ).filter(
            (ChatRoom.user_id == user_id) | (ChatRoom.guide_id == user_id)
        ).first()
        
        if not chat_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat room not found"
            )
        
        return chat_room
    
    @staticmethod
    def delete_matching_request(
        db: Session,
        matching_id: str,
        user_id: str
    ) -> bool:
        """매칭 요청 삭제 (사용자 또는 가이드)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Starting delete_matching_request: matching_id={matching_id}, user_id={user_id}")
        
        # 매칭 요청 조회
        matching_request = db.query(MatchingRequest).filter(
            MatchingRequest.id == matching_id
        ).first()
        
        if not matching_request:
            logger.error(f"Matching request not found: {matching_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Matching request not found"
            )
        
        logger.info(f"Found matching request: user_id={matching_request.user_id}, guide_id={matching_request.guide_id}")
        
        # 권한 확인 - 요청자이거나 가이드인 경우만 삭제 가능
        guide = db.query(Guide).filter(Guide.id == matching_request.guide_id).first()
        if matching_request.user_id != user_id and guide.user_id != user_id:
            logger.error(f"Permission denied: user_id={user_id} is not the requester or guide")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this matching"
            )
        
        # 관련 채팅방 찾기
        chat_room = db.query(ChatRoom).filter(
            ChatRoom.matching_request_id == matching_id
        ).first()
        
        if chat_room:
            logger.info(f"Found chat room: {chat_room.id}")
            
            # 채팅 메시지 삭제
            deleted_messages = db.query(ChatMessage).filter(
                ChatMessage.chat_room_id == chat_room.id
            ).delete()
            logger.info(f"Deleted {deleted_messages} chat messages")
            
            # 채팅방 삭제
            db.delete(chat_room)
            logger.info("Deleted chat room")
        else:
            logger.info("No chat room found for this matching request")
        
        # 매칭 요청 삭제
        db.delete(matching_request)
        logger.info("Deleted matching request")
        
        db.commit()
        logger.info("Transaction committed successfully")
        
        return True
    
    @staticmethod
    def get_user_chat_rooms(
        db: Session,
        user_id: str
    ) -> List[ChatRoom]:
        """사용자의 채팅방 목록 조회"""
        return db.query(ChatRoom).filter(
            (ChatRoom.user_id == user_id) | (ChatRoom.guide_id == user_id),
            ChatRoom.is_active == True
        ).order_by(ChatRoom.last_message_at.desc().nullslast()).all()
    
    @staticmethod
    def send_message(
        db: Session,
        room_id: str,
        sender_id: str,
        message: str
    ) -> ChatMessage:
        """메시지 전송"""
        # 채팅방 확인
        chat_room = db.query(ChatRoom).filter(
            ChatRoom.id == room_id,
            ChatRoom.is_active == True
        ).first()
        
        if not chat_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat room not found"
            )
        
        # 권한 확인
        if sender_id not in [chat_room.user_id, chat_room.guide_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this chat room"
            )
        
        # 수신자 ID 결정
        receiver_id = chat_room.guide_id if sender_id == chat_room.user_id else chat_room.user_id
        
        # 메시지 생성
        chat_message = ChatMessage(
            chat_room_id=room_id,
            matching_request_id=chat_room.matching_request_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )
        db.add(chat_message)
        
        # 채팅방 최근 메시지 업데이트
        chat_room.last_message = message
        chat_room.last_message_at = datetime.now()
        
        db.commit()
        db.refresh(chat_message)
        
        return chat_message
    
    @staticmethod
    def get_chat_messages(
        db: Session,
        room_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """채팅 메시지 조회"""
        # 채팅방 권한 확인
        chat_room = MatchingService.get_chat_room(db, room_id, user_id)
        
        # 메시지 조회
        messages = db.query(ChatMessage).filter(
            ChatMessage.chat_room_id == room_id
        ).order_by(ChatMessage.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()
        
        # 읽음 처리
        unread_messages = [msg for msg in messages if msg.receiver_id == user_id and not msg.is_read]
        for msg in unread_messages:
            msg.is_read = True
        
        if unread_messages:
            db.commit()
        
        return list(reversed(messages))

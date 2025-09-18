from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import json
import logging
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user_ws
from app.models.user import User
from app.models.chat import ChatRoom
from app.models.matching import ChatMessage
from app.websocket.chat_websocket import manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """버WebSocket 채팅 엔드포인트"""
    user = None
    
    try:
        # WebSocket 연결 수락 (인증 전)
        await websocket.accept()
        logger.info("[WebSocket] Connection accepted")
        
        # URL에서 토큰 추출
        query_params = websocket.url.query
        logger.info(f"[WebSocket] Query params: {query_params}")
        
        token = None
        if query_params:
            import urllib.parse
            params = urllib.parse.parse_qs(query_params)
            token = params.get('token', [None])[0]
            logger.info(f"[WebSocket] Token extracted: {token[:20] if token else 'None'}...")
        
        if not token:
            logger.error("No token provided in WebSocket connection")
            await websocket.close(code=4001, reason="No token provided")
            return
        
        # 토큰으로 사용자 인증
        user = await get_current_user_ws(token, db)
        if not user:
            logger.error(f"Invalid token or user not found")
            await websocket.close(code=4001, reason="Unauthorized")
            return
        
        logger.info(f"[WebSocket] User authenticated: {user.id} ({user.nickname})")
        
        # ConnectionManager에 연결 등록
        await manager.connect(websocket, user.id)
        logger.info(f"[WebSocket] User connected to manager: {user.id}")
        
        # 연결 성공 메시지 전송
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "user_id": user.id,
            "message": "Successfully connected to chat server"
        })
        
        # 메시지 수신 대기
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                data = await websocket.receive_json()
                logger.info(f"[WebSocket] Received message from {user.id}: {data}")
                
                action = data.get("action")
                logger.info(f"[WebSocket] Action: {action}")
                
                if action == "join_room":
                    room_id = data.get("room_id")
                    if room_id:
                        logger.info(f"[WebSocket] User {user.id} joining room {room_id}")
                        await websocket.send_json({
                            "type": "room_joined",
                            "room_id": room_id,
                            "message": f"Joined room {room_id}"
                        })
                elif action == "leave_room":
                    room_id = data.get("room_id")
                    if room_id:
                        logger.info(f"[WebSocket] User {user.id} leaving room {room_id}")
                        await websocket.send_json({
                            "type": "room_left",
                            "room_id": room_id,
                            "message": f"Left room {room_id}"
                        })
                elif action == "send_message":
                    await handle_chat_message(data, user, db)
                elif action == "ping":
                    await websocket.send_json({"type": "pong"})
                elif action == "read_receipt":
                    await handle_read_receipt(data, user, db)
                else:
                    # 이전 버전 호환성을 위한 처리
                    message_type = data.get("type")
                    if message_type == "message":
                        await handle_chat_message(data, user, db)
                    elif message_type == "read_receipt":
                        await handle_read_receipt(data, user, db)
                    else:
                        logger.warning(f"[WebSocket] Unknown action/type: {action}/{message_type}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user: {user.id}")
                break
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received from user: {user.id}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid message format"
                })
            except Exception as e:
                logger.error(f"Error handling message from user {user.id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket.client_state.value == 1:  # WebSocket is connected
            await websocket.close(code=4000, reason=str(e))
    finally:
        if user:
            manager.disconnect(websocket)
            logger.info(f"Cleaned up connection for user: {user.id}")


async def handle_chat_message(data: dict, sender: User, db: Session):
    """채팅 메시지 처리 - 이미 저장된 메시지를 WebSocket으로 브로드캐스트"""
    logger.info(f"[handle_chat_message] This function should not be called from Flutter app")
    # Flutter 앱에서는 이 함수를 호출하지 않음 - API를 통해 메시지 전송
    pass


async def handle_read_receipt(data: dict, user: User, db: Session):
    """읽음 처리"""
    try:
        room_id = data.get("room_id")
        message_ids = data.get("message_ids", [])
        
        if not room_id or not message_ids:
            return
        
        # 메시지 읽음 처리
        db.query(ChatMessage).filter(
            ChatMessage.id.in_(message_ids),
            ChatMessage.receiver_id == user.id,
            ChatMessage.is_read == False
        ).update({"is_read": True}, synchronize_session=False)
        
        db.commit()
        
        # 읽음 확인 전송
        # 채팅방의 다른 사용자 찾기
        chat_room = db.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        if chat_room:
            other_user_id = chat_room.guide_id if user.id == chat_room.user_id else chat_room.user_id
            
            await manager.send_personal_message({
                "type": "read_receipt",
                "room_id": room_id,
                "message_ids": message_ids,
                "reader_id": user.id
            }, other_user_id)
        
    except Exception as e:
        logger.error(f"Error handling read receipt: {e}")

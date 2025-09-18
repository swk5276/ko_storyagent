from typing import Dict, Set
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # WebSocket -> user_id (역참조용)
        self.connection_to_user: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """WebSocket 연결 저장 (연결은 이미 수락됨)"""
        # websocket.accept()는 호출하지 않음 (이미 위에서 호출됨)
        
        # 사용자의 연결 목록에 추가
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # 역참조 매핑 추가
        self.connection_to_user[websocket] = user_id
        
        logger.info(f"User {user_id} connected. Total connections for this user: {len(self.active_connections[user_id])}")
        logger.info(f"Total connected users: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """WebSocket 연결 해제"""
        # 역참조로 user_id 찾기
        user_id = self.connection_to_user.get(websocket)
        if user_id:
            # 연결 목록에서 제거
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # 해당 사용자의 모든 연결이 끊어졌으면 목록에서 제거
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            
            # 역참조 매핑 제거
            del self.connection_to_user[websocket]
            
            logger.info(f"User {user_id} disconnected")

    async def send_personal_message(self, message: dict, user_id: str):
        """특정 사용자에게 메시지 전송"""
        if user_id in self.active_connections:
            # 해당 사용자의 모든 연결에 메시지 전송
            disconnected_sockets = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected_sockets.append(connection)
            
            # 연결이 끊어진 소켓 제거
            for socket in disconnected_sockets:
                self.disconnect(socket)

    async def send_to_chat_room(self, message: dict, sender_id: str, receiver_id: str):
        """채팅방의 모든 참여자에게 메시지 전송"""
        # 발신자와 수신자 모두에게 전송
        for user_id in [sender_id, receiver_id]:
            await self.send_personal_message(message, user_id)

    def get_user_connection_count(self, user_id: str) -> int:
        """특정 사용자의 활성 연결 수 반환"""
        return len(self.active_connections.get(user_id, set()))

    def is_user_online(self, user_id: str) -> bool:
        """사용자가 온라인인지 확인"""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# 전역 연결 관리자 인스턴스
manager = ConnectionManager()

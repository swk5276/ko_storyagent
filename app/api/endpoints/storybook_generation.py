from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from typing import Optional, List
import os
import random
import logging
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate")
async def generate_storybook(
    input_type: str = Form(...),  # "audio_upload", "audio_record", "text"
    text_content: Optional[str] = Form(None),
    image_style: str = Form(...),  # "pixar", "cyberpunk", "ghibli"
    character_description: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    character_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user)
):
    """
    스토리북 생성 API
    - input_type: 입력 방식 (audio_upload, audio_record, text)
    - text_content: 텍스트 입력 시 내용
    - image_style: 이미지 스타일 (pixar, cyberpunk, ghibli)
    - character_description: 등장인물 설명
    - audio_file: 오디오 파일 (녹음 업로드 시)
    - character_image: 캐릭터 이미지 (선택사항)
    """
    
    logger.info(f"Storybook generation request from user {current_user.id}")
    logger.info(f"Input type: {input_type}, Image style: {image_style}")
    
    # 요청 데이터 로깅
    if input_type == "text" and text_content:
        logger.info(f"Text content: {text_content[:100]}...")
    elif input_type in ["audio_upload", "audio_record"] and audio_file:
        logger.info(f"Audio file received: {audio_file.filename}")
    
    if character_image:
        logger.info(f"Character image received: {character_image.filename}")
    
    if character_description:
        logger.info(f"Character description: {character_description}")
    
    # 테스트 비디오 디렉토리 확인
    test_video_dir = os.path.join("test", "test_video")
    if not os.path.exists(test_video_dir):
        raise HTTPException(status_code=500, detail="Test video directory not found")
    
    # 테스트 비디오 파일 목록 가져오기
    video_files = [f for f in os.listdir(test_video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    if not video_files:
        # 테스트 비디오가 없으면 기본 응답
        logger.warning("No test videos found in directory")
        return {
            "status": "success",
            "message": "Test mode - no video available",
            "video_url": None,
            "generation_id": "test_" + str(random.randint(1000, 9999))
        }
    
    # 랜덤하게 테스트 비디오 선택
    selected_video = random.choice(video_files)
    video_url = f"/test/test_video/{selected_video}"
    
    logger.info(f"Returning test video: {selected_video}")
    
    return {
        "status": "success",
        "message": "Storybook generated successfully (test mode)",
        "video_url": video_url,
        "generation_id": "test_" + str(random.randint(1000, 9999)),
        "metadata": {
            "input_type": input_type,
            "image_style": image_style,
            "has_character_image": character_image is not None,
            "has_character_description": character_description is not None
        }
    }

@router.get("/generation/{generation_id}")
async def get_generation_status(
    generation_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    생성 상태 확인 API (테스트용)
    """
    # 테스트 모드에서는 항상 완료 상태 반환
    return {
        "generation_id": generation_id,
        "status": "completed",
        "progress": 100,
        "message": "Generation completed (test mode)"
    }

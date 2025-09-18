# FastAPI 서버의 비디오 썸네일 생성 예제

# requirements.txt에 추가
# opencv-python==4.8.1.78
# pillow==10.1.0

import cv2
from PIL import Image
import os
from pathlib import Path

async def generate_video_thumbnail(video_path: str, output_path: str, time_seconds: float = 1.0):
    """
    비디오 파일에서 특정 시간의 프레임을 추출하여 썸네일 생성
    
    Args:
        video_path: 비디오 파일 경로
        output_path: 썸네일 저장 경로
        time_seconds: 추출할 프레임의 시간 (초)
    """
    try:
        # 비디오 캡처 객체 생성
        cap = cv2.VideoCapture(video_path)
        
        # FPS 가져오기
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 특정 프레임으로 이동
        frame_number = int(fps * time_seconds)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        # 프레임 읽기
        ret, frame = cap.read()
        
        if ret:
            # BGR을 RGB로 변환
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # PIL Image로 변환
            image = Image.fromarray(frame_rgb)
            
            # 썸네일 크기 조정 (720p)
            thumbnail_size = (720, 1280)  # 9:16 비율
            image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            
            # 썸네일 저장
            image.save(output_path, "JPEG", quality=85)
            
            cap.release()
            return True
        
        cap.release()
        return False
        
    except Exception as e:
        print(f"썸네일 생성 실패: {e}")
        return False

# FastAPI 엔드포인트에서 사용
from fastapi import UploadFile, File
import aiofiles
import uuid

@router.post("/stories")
async def create_story(
    title: str = Form(...),
    content: str = Form(None),
    media_file: UploadFile = File(...),
    # ... 기타 필드들
):
    # 파일 저장
    file_extension = media_file.filename.split(".")[-1]
    file_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"uploads/media/{file_name}"
    
    # 파일 저장
    async with aiofiles.open(file_path, 'wb') as f:
        content = await media_file.read()
        await f.write(content)
    
    # 비디오인 경우 썸네일 생성
    thumbnail_url = None
    if file_extension.lower() in ['mp4', 'avi', 'mov', 'mkv']:
        thumbnail_name = f"{uuid.uuid4()}.jpg"
        thumbnail_path = f"uploads/thumbnails/{thumbnail_name}"
        
        # 썸네일 생성 (1초 지점의 프레임 추출)
        success = await generate_video_thumbnail(file_path, thumbnail_path, 1.0)
        
        if success:
            thumbnail_url = f"/uploads/thumbnails/{thumbnail_name}"
    
    # DB에 저장
    story = Story(
        title=title,
        content=content,
        media_url=f"/uploads/media/{file_name}",
        thumbnail_url=thumbnail_url,
        media_type="video" if file_extension.lower() in ['mp4', 'avi', 'mov', 'mkv'] else "image",
        # ... 기타 필드들
    )
    
    # ... DB 저장 로직

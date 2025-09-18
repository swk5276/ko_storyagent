import cv2
from PIL import Image
import os
from pathlib import Path
import uuid
from typing import Optional

class ThumbnailService:
    """비디오 및 이미지 썸네일 생성 서비스"""
    
    def __init__(self, thumbnails_dir: str = "uploads/thumbnails"):
        self.thumbnails_dir = thumbnails_dir
        os.makedirs(thumbnails_dir, exist_ok=True)
    
    async def generate_video_thumbnail(
        self, 
        video_path: str, 
        time_seconds: float = 1.0,
        size: tuple = (720, 1280)
    ) -> Optional[str]:
        """
        비디오 파일에서 특정 시간의 프레임을 추출하여 썸네일 생성
        
        Args:
            video_path: 비디오 파일 경로
            time_seconds: 추출할 프레임의 시간 (초)
            size: 썸네일 크기 (width, height)
        
        Returns:
            썸네일 파일 경로 (실패 시 None)
        """
        cap = None
        try:
            print(f"비디오 썸네일 생성 시도: {video_path}")
            
            # 파일 존재 확인
            if not os.path.exists(video_path):
                print(f"비디오 파일이 존재하지 않습니다: {video_path}")
                return None
            
            # 비디오 캡처 객체 생성
            cap = cv2.VideoCapture(video_path)
            
            # 비디오가 제대로 열렸는지 확인
            if not cap.isOpened():
                print(f"비디오 파일을 열 수 없습니다: {video_path}")
                return None
            
            # FPS와 총 프레임 수 가져오기
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps == 0:
                fps = 30  # 기본값
            
            # 특정 프레임으로 이동 (조금 더 안전하게)
            frame_number = min(int(fps * time_seconds), total_frames - 1)
            frame_number = max(0, frame_number)  # 음수 방지
            
            # 첫 번째 시도
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            # 첫 번째 시도 실패 시 첫 프레임 사용
            if not ret and frame_number > 0:
                print(f"지정된 프레임({frame_number}) 읽기 실패, 첫 프레임 사용")
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            
            if ret and frame is not None:
                # BGR을 RGB로 변환
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # PIL Image로 변환
                image = Image.fromarray(frame_rgb)
                
                # 9:16 비율로 크롭 (세로 형식)
                width, height = image.size
                target_ratio = 9 / 16
                current_ratio = width / height
                
                if current_ratio > target_ratio:
                    # 현재 이미지가 더 넓은 경우
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    image = image.crop((left, 0, left + new_width, height))
                else:
                    # 현재 이미지가 더 좁은 경우
                    new_height = int(width / target_ratio)
                    top = (height - new_height) // 2
                    image = image.crop((0, top, width, top + new_height))
                
                # 크기 조정
                image = image.resize(size, Image.Resampling.LANCZOS)
                
                # 썸네일 파일명 생성
                thumbnail_filename = f"{uuid.uuid4()}.jpg"
                thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
                
                # 썸네일 저장
                image.save(thumbnail_path, "JPEG", quality=85, optimize=True)
                
                print(f"비디오 썸네일 생성 성공: {thumbnail_path}")
                cap.release()
                return thumbnail_path
            else:
                print("프레임 읽기 실패")
            
            cap.release()
            return None
            
        except Exception as e:
            print(f"비디오 썸네일 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            if cap is not None:
                cap.release()
            return None
    
    async def generate_image_thumbnail(
        self, 
        image_path: str,
        size: tuple = (720, 1280)
    ) -> Optional[str]:
        """
        이미지 파일에서 썸네일 생성
        
        Args:
            image_path: 이미지 파일 경로
            size: 썸네일 크기 (width, height)
        
        Returns:
            썸네일 파일 경로 (실패 시 None)
        """
        try:
            print(f"이미지 썸네일 생성 시도: {image_path}")
            
            # 파일 존재 확인
            if not os.path.exists(image_path):
                print(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None
            
            # 이미지 열기
            with Image.open(image_path) as image:
                # EXIF 정보를 활용한 자동 회전
                if hasattr(image, '_getexif'):
                    exif = image._getexif()
                    if exif:
                        orientation = exif.get(0x0112)
                        if orientation:
                            rotations = {
                                3: 180,
                                6: 270,
                                8: 90
                            }
                            if orientation in rotations:
                                image = image.rotate(rotations[orientation], expand=True)
                
                # RGB로 변환 (RGBA 이미지 처리)
                if image.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1])
                    image = background
                elif image.mode not in ('RGB', 'L'):
                    image = image.convert('RGB')
                
                # 9:16 비율로 크롭 (세로 형식)
                width, height = image.size
                target_ratio = 9 / 16
                current_ratio = width / height
                
                if current_ratio > target_ratio:
                    # 현재 이미지가 더 넓은 경우
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    image = image.crop((left, 0, left + new_width, height))
                else:
                    # 현재 이미지가 더 좁은 경우
                    new_height = int(width / target_ratio)
                    top = (height - new_height) // 2
                    image = image.crop((0, top, width, top + new_height))
                
                # 크기 조정
                image = image.resize(size, Image.Resampling.LANCZOS)
                
                # 썸네일 파일명 생성
                thumbnail_filename = f"{uuid.uuid4()}.jpg"
                thumbnail_path = os.path.join(self.thumbnails_dir, thumbnail_filename)
                
                # 썸네일 저장
                image.save(thumbnail_path, "JPEG", quality=85, optimize=True)
                
                print(f"이미지 썸네일 생성 성공: {thumbnail_path}")
                return thumbnail_path
                
        except Exception as e:
            print(f"이미지 썸네일 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None

# 싱글톤 인스턴스
thumbnail_service = ThumbnailService()

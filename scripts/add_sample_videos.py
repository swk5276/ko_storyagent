import os
import shutil
import requests

def download_sample_video():
    """샘플 비디오 다운로드 또는 더미 파일 생성"""
    upload_dir = os.path.join("..", "uploads", "stories")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 샘플 비디오 파일 생성 (실제로는 비디오가 아니지만 테스트용)
    sample_videos = [
        "sample_story_1.mp4",
        "sample_story_2.mp4",
        "sample_story_3.mp4"
    ]
    
    for video_name in sample_videos:
        video_path = os.path.join(upload_dir, video_name)
        if not os.path.exists(video_path):
            # 더미 파일 생성 (실제 프로덕션에서는 실제 비디오 파일 사용)
            with open(video_path, "wb") as f:
                f.write(b"This is a dummy video file for testing purposes.")
            print(f"Created sample video: {video_name}")
        else:
            print(f"Sample video already exists: {video_name}")

if __name__ == "__main__":
    download_sample_video()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.api import api_router
from app.api.endpoints.websocket import router as websocket_router
from app.core.config import settings
from app.core.database import engine, Base
import logging
import time
import os

# 모든 모델 import (테이블 자동 생성을 위해)
from app.models import user, story, guide, matching, chat, bookmark, region, report

# 테이블 자동 생성
Base.metadata.create_all(bind=engine)
# uvicorn main:app --host=0.0.0.0 --port=8005 --reload
# python -m uvicorn main:app --host=0.0.0.0 --port=8005 --reload


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Story Book API",
    description="관광 문화 SNS 앱 API",
    version="1.0.0"
)

# 422 에러 핸들러
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc.errors()}")
    logger.error(f"Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 임시로 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # 요청 로깅
    logger.info(f"Request: {request.method} {request.url.path}")
    if request.url.path.startswith("/uploads/"):
        logger.info(f"Static file request: {request.url.path}")
        # 실제 파일 경로 확인
        file_path = os.path.join(".", request.url.path.lstrip("/"))
        logger.info(f"Looking for file at: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
    
    # 422 에러 디버깅을 위한 요청 본문 로깅
    if request.method == "POST" and request.url.path.endswith("/report"):
        body = await request.body()
        logger.info(f"Request body: {body}")
        # 요청 본문을 다시 설정 (consume되었으므로)
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    
    response = await call_next(request)
    
    # 응답 로깅
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
    
    # 422 에러인 경우 상세 로그
    if response.status_code == 422:
        logger.error(f"422 Error for {request.method} {request.url.path}")
    
    return response

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")

# WebSocket 라우터 등록 - /api/v1 prefix에 포함
app.include_router(websocket_router, prefix="/api/v1")

# 정적 파일 서빙 (업로드된 파일)
# 디렉토리 존재 확인 및 생성
import os

uploads_dir = "uploads"
stories_dir = os.path.join(uploads_dir, "stories")
thumbnails_dir = os.path.join(uploads_dir, "thumbnails")

# 디렉토리 생성
for dir_path in [uploads_dir, stories_dir, thumbnails_dir]:
    os.makedirs(dir_path, exist_ok=True)
    logger.info(f"Directory ensured: {dir_path}")

# 정적 파일 마운트 - 더 구체적인 경로를 먼저 마운트
# 각 하위 디렉토리를 먼저 마운트
app.mount("/uploads/thumbnails", StaticFiles(directory=thumbnails_dir, html=False), name="thumbnails")
app.mount("/uploads/stories", StaticFiles(directory=stories_dir, html=False), name="stories")

# 그 다음 전체 uploads 디렉토리 마운트
app.mount("/uploads", StaticFiles(directory=uploads_dir, html=False), name="uploads")

# 테스트 비디오 디렉토리 마운트
test_video_dir = os.path.join("test", "test_video")
os.makedirs(test_video_dir, exist_ok=True)
app.mount("/test/test_video", StaticFiles(directory=test_video_dir, html=False), name="test_videos")

logger.info(f"Static files mounted: /uploads/thumbnails -> {thumbnails_dir}")
logger.info(f"Static files mounted: /uploads/stories -> {stories_dir}")
logger.info(f"Static files mounted: /uploads -> {uploads_dir}")

# 정적 파일에 대한 CORS 헤더 추가
@app.middleware("http")
async def add_cors_headers_for_static(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/uploads/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)

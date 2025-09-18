from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import Optional, List, Dict, Any
from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.core import security as auth_service
from app.core.region_data import REGION_DATA, get_cities_by_category
from app.models.story import Story, StoryLike, StoryComment
from app.models.bookmark import StoryBookmark
from app.models.user import User
from app.models.region import Region
from app.models.guide import Guide
from app.models import user as user_models
from app.models import guide as guide_models
from app.schemas.story import (
    StoryCreate, StoryUpdate, StoryResponse, StoryListResponse,
    CommentCreate, CommentResponse, LikeToggleResponse, SortOrder,
    StoryReportCreate
)
from app.services.thumbnail_service import thumbnail_service
import uuid
import os
from datetime import datetime

router = APIRouter()

# 파일 업로드 설정
UPLOAD_DIR = "uploads/stories"
THUMBNAIL_DIR = "uploads/thumbnails"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(THUMBNAIL_DIR, exist_ok=True)

@router.get("/my", response_model=Dict[str, Any])
async def get_my_stories(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    현재 사용자가 업로드한 스토리 목록 조회
    """
    # 가이드 확인
    guide = db.query(Guide).filter(
        Guide.user_id == current_user.id
    ).first()
    
    if not guide:
        raise HTTPException(
            status_code=403,
            detail="가이드만 스토리를 조회할 수 있습니다"
        )
    
    # 내 스토리 목록 조회
    stories = db.query(Story).filter(
        Story.user_id == current_user.id,
        Story.is_active == True
    ).order_by(
        Story.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # 스토리 데이터 가공
    stories_data = []
    for story in stories:
        # 지역 정보 - region_id1과 region_id2를 사용
        region_name = None
        if story.region_id1 and story.region_id2:
            region_name = f"{story.region_id1} {story.region_id2}"
        
        story_dict = {
            "id": story.id,
            "title": story.title,
            "content": story.content,
            "media_type": story.media_type,
            "media_url": story.media_url,
            "thumbnail_url": story.thumbnail_url,
            "category": story.category,
            "view_count": story.view_count,
            "like_count": story.like_count,
            "is_active": story.is_active,
            "created_at": story.created_at.isoformat() if hasattr(story.created_at, 'isoformat') else str(story.created_at),
            "updated_at": story.updated_at.isoformat() if hasattr(story.updated_at, 'isoformat') else str(story.updated_at),
            "user_id": story.user_id,
            "user_nickname": current_user.nickname,
            "user_profile_image": current_user.profile_image,
            "guide_id": story.guide_id,
            "region_id": story.region_id1,
            "region_name": region_name
        }
        stories_data.append(story_dict)
    
    return {
        "stories": stories_data,
        "total": db.query(Story).filter(
            Story.user_id == current_user.id,
            Story.is_active == True
        ).count(),
        "skip": skip,
        "limit": limit
    }

@router.get("/", response_model=StoryListResponse)
async def get_stories(
    region_category: Optional[str] = None,  # 수도권, 강원 등
    city: Optional[str] = None,  # 서울, 부산 등
    sort: SortOrder = SortOrder.latest,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """스토리 목록 조회 (홈 화면)"""
    query = db.query(Story).filter(Story.is_active == True)
    
    # 지역 필터
    if region_category:
        # 지역 카테고리(수도권, 강원 등)로 필터링
        query = query.filter(Story.region_id1 == region_category)
    elif city:
        # 특정 도시로 필터링
        query = query.filter(Story.region_id2 == city)
    
    # 정렬
    if sort == SortOrder.popular:
        query = query.order_by(desc(Story.like_count), desc(Story.view_count))
    else:
        query = query.order_by(desc(Story.created_at))
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    stories_db = query.offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    stories = []
    for story in stories_db:
        # 작성자 정보
        author = db.query(User).filter(User.id == story.user_id).first()
        
        # 지역 정보
        region_name = None
        if story.region_id1 and story.region_id2:
            region_name = f"{story.region_id1} {story.region_id2}"
        
        # 좋아요 여부
        is_liked = False
        if current_user:
            like = db.query(StoryLike).filter(
                and_(StoryLike.user_id == current_user.id, StoryLike.story_id == story.id)
            ).first()
            is_liked = like is not None
        
        # 북마크 여부
        is_bookmarked = False
        if current_user:
            bookmark = db.query(StoryBookmark).filter(
                and_(StoryBookmark.user_id == current_user.id, StoryBookmark.story_id == story.id)
            ).first()
            is_bookmarked = bookmark is not None
        
        # 댓글 수
        comments_count = db.query(StoryComment).filter(StoryComment.story_id == story.id).count()
        
        stories.append(StoryResponse(
            id=story.id,
            user_id=story.user_id,
            guide_id=story.guide_id,
            title=story.title,
            content=story.content,
            media_type=story.media_type,
            media_url=story.media_url,
            thumbnail_url=story.thumbnail_url,
            category=story.category,
            region_id=story.region_id1,
            view_count=story.view_count,
            like_count=story.like_count,
            is_active=story.is_active,
            created_at=datetime.fromisoformat(story.created_at) if isinstance(story.created_at, str) else story.created_at,
            updated_at=datetime.fromisoformat(story.updated_at) if isinstance(story.updated_at, str) else story.updated_at,
            author_nickname=author.nickname if author else "Unknown",
            author_profile_image=author.profile_image if author else None,
            region_name=region_name,
            is_liked=is_liked,
            is_bookmarked=is_bookmarked,
            comments_count=comments_count
        ))
    
    return StoryListResponse(
        stories=stories,
        total=total,
        page=page,
        limit=limit
    )

@router.post("/", response_model=StoryResponse)
async def create_story(
    story: StoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """스토리 생성 (가이드만 가능)"""
    print(f"Story creation request from user: {current_user.id}")
    print(f"Story data: {story.dict()}")
    
    # 가이드 권한 확인
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if not guide or not guide.is_approved:
        raise HTTPException(status_code=403, detail="Only approved guides can create stories")
    
    # 스토리 생성
    db_story = Story(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        guide_id=guide.id,
        title=story.title,
        content=story.content,
        media_type=story.media_type,
        media_url=story.media_url,
        thumbnail_url=story.thumbnail_url,
        category=story.category,
        region_id1=story.region_id1,
        region_id2=story.region_id2,
        view_count=0,
        like_count=0,
        is_active=True
    )
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    
    # 응답 데이터
    region_name = None
    if db_story.region_id1 and db_story.region_id2:
        region_name = f"{db_story.region_id1} {db_story.region_id2}"
    
    return StoryResponse(
        id=db_story.id,
        user_id=db_story.user_id,
        guide_id=db_story.guide_id,
        title=db_story.title,
        content=db_story.content,
        media_type=db_story.media_type,
        media_url=db_story.media_url,
        thumbnail_url=db_story.thumbnail_url,
        category=db_story.category,
        region_id=db_story.region_id1,  # 이전 버전 호환성
        view_count=db_story.view_count,
        like_count=db_story.like_count,
        is_active=db_story.is_active,
        created_at=datetime.fromisoformat(db_story.created_at) if isinstance(db_story.created_at, str) else db_story.created_at,
        updated_at=datetime.fromisoformat(db_story.updated_at) if isinstance(db_story.updated_at, str) else db_story.updated_at,
        author_nickname=current_user.nickname,
        author_profile_image=current_user.profile_image,
        region_name=region_name,
        is_liked=False,
        comments_count=0
    )

@router.get("/{story_id}", response_model=StoryResponse)
async def get_story(
    story_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """스토리 상세 조회"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # 조회수 증가
    story.view_count += 1
    db.commit()
    
    # 작성자 정보
    author = db.query(User).filter(User.id == story.user_id).first()
    
    # 지역 정보
    region_name = None
    if story.region_id1 and story.region_id2:
        region_name = f"{story.region_id1} {story.region_id2}"
    
    # 좋아요 여부
    is_liked = False
    if current_user:
        like = db.query(StoryLike).filter(
            and_(StoryLike.user_id == current_user.id, StoryLike.story_id == story.id)
        ).first()
        is_liked = like is not None
    
    # 댓글 수
    comments_count = db.query(StoryComment).filter(StoryComment.story_id == story.id).count()
    
    return StoryResponse(
        id=story.id,
        user_id=story.user_id,
        guide_id=story.guide_id,
        title=story.title,
        content=story.content,
        media_type=story.media_type,
        media_url=story.media_url,
        thumbnail_url=story.thumbnail_url,
        category=story.category,
        region_id=story.region_id1,
        view_count=story.view_count,
        like_count=story.like_count,
        is_active=story.is_active,
        created_at=datetime.fromisoformat(story.created_at) if isinstance(story.created_at, str) else story.created_at,
        updated_at=datetime.fromisoformat(story.updated_at) if isinstance(story.updated_at, str) else story.updated_at,
        author_nickname=author.nickname if author else "Unknown",
        author_profile_image=author.profile_image if author else None,
        region_name=region_name,
        is_liked=is_liked,
        comments_count=comments_count
    )

@router.post("/{story_id}/like", response_model=LikeToggleResponse)
async def toggle_like(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """좋아요 토글"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # 기존 좋아요 확인
    existing_like = db.query(StoryLike).filter(
        and_(StoryLike.user_id == current_user.id, StoryLike.story_id == story_id)
    ).first()
    
    if existing_like:
        # 좋아요 취소
        db.delete(existing_like)
        story.like_count = max(0, story.like_count - 1)
        is_liked = False
    else:
        # 좋아요 추가
        new_like = StoryLike(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            story_id=story_id
        )
        db.add(new_like)
        story.like_count += 1
        is_liked = True
    
    db.commit()
    
    return LikeToggleResponse(
        is_liked=is_liked,
        like_count=story.like_count
    )

@router.get("/{story_id}/comments", response_model=List[CommentResponse])
async def get_comments(
    story_id: str,
    db: Session = Depends(get_db)
):
    """댓글 목록 조회"""
    # 부모 댓글만 먼저 조회
    parent_comments = db.query(StoryComment).filter(
        and_(StoryComment.story_id == story_id, StoryComment.parent_id == None)
    ).order_by(desc(StoryComment.created_at)).all()
    
    comments = []
    for comment in parent_comments:
        # 댓글 작성자 정보
        user = db.query(User).filter(User.id == comment.user_id).first()
        
        # 대댓글 조회
        replies = []
        child_comments = db.query(StoryComment).filter(
            StoryComment.parent_id == comment.id
        ).order_by(StoryComment.created_at).all()
        
        for reply in child_comments:
            reply_user = db.query(User).filter(User.id == reply.user_id).first()
            replies.append(CommentResponse(
                id=reply.id,
                story_id=reply.story_id,
                user_id=reply.user_id,
                user_nickname=reply_user.nickname if reply_user else "Unknown",
                user_profile_image=reply_user.profile_image if reply_user else None,
                content=reply.content,
                parent_id=reply.parent_id,
                created_at=datetime.fromisoformat(reply.created_at) if isinstance(reply.created_at, str) else reply.created_at,
                updated_at=datetime.fromisoformat(reply.updated_at) if isinstance(reply.updated_at, str) else reply.updated_at,
                replies=[]
            ))
        
        comments.append(CommentResponse(
            id=comment.id,
            story_id=comment.story_id,
            user_id=comment.user_id,
            user_nickname=user.nickname if user else "Unknown",
            user_profile_image=user.profile_image if user else None,
            content=comment.content,
            parent_id=comment.parent_id,
            created_at=datetime.fromisoformat(comment.created_at) if isinstance(comment.created_at, str) else comment.created_at,
            updated_at=datetime.fromisoformat(comment.updated_at) if isinstance(comment.updated_at, str) else comment.updated_at,
            replies=replies
        ))
    
    return comments

@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """스토리 삭제 (작성자 본인만 가능)"""
    # 스토리 확인
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # 작성자 본인 확인
    if story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own stories")
    
    # 파일 경로 저장 (삭제용)
    media_file_path = None
    thumbnail_file_path = None
    
    # media_url에서 파일 경로 추출
    if story.media_url:
        # /uploads/stories/filename.ext 형식에서 파일명 추출
        media_filename = story.media_url.split('/')[-1]
        media_file_path = os.path.join(UPLOAD_DIR, media_filename)
    
    # thumbnail_url에서 파일 경로 추출
    if story.thumbnail_url:
        thumbnail_filename = story.thumbnail_url.split('/')[-1]
        thumbnail_file_path = os.path.join(THUMBNAIL_DIR, thumbnail_filename)
    
    try:
        # 1. 관련 데이터 삭제
        # 댓글 삭제
        db.query(StoryComment).filter(StoryComment.story_id == story_id).delete()
        
        # 좋아요 삭제
        db.query(StoryLike).filter(StoryLike.story_id == story_id).delete()
        
        # 지역 스토리 수 감소 (구 버전 호환성)
        # 새 버전에서는 region 테이블을 사용하지 않음
        
        # 스토리 삭제
        db.delete(story)
        db.commit()
        
        # 2. 파일 삭제
        # 미디어 파일 삭제
        if media_file_path and os.path.exists(media_file_path):
            os.remove(media_file_path)
            print(f"미디어 파일 삭제: {media_file_path}")
        
        # 썸네일 파일 삭제
        if thumbnail_file_path and os.path.exists(thumbnail_file_path):
            os.remove(thumbnail_file_path)
            print(f"썸네일 파일 삭제: {thumbnail_file_path}")
        
        return {"message": "Story deleted successfully"}
        
    except Exception as e:
        db.rollback()
        print(f"스토리 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete story")



@router.post("/{story_id}/comments", response_model=CommentResponse)
async def create_comment(
    story_id: str,
    comment: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """댓글 작성"""
    # 스토리 확인
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # 부모 댓글 확인
    if comment.parent_id:
        parent = db.query(StoryComment).filter(StoryComment.id == comment.parent_id).first()
        if not parent or parent.story_id != story_id:
            raise HTTPException(status_code=400, detail="Invalid parent comment")
    
    # 댓글 생성
    db_comment = StoryComment(
        id=str(uuid.uuid4()),
        story_id=story_id,
        user_id=current_user.id,
        **comment.dict()
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return CommentResponse(
        id=db_comment.id,
        story_id=db_comment.story_id,
        user_id=db_comment.user_id,
        user_nickname=current_user.nickname,
        user_profile_image=current_user.profile_image,
        content=db_comment.content,
        parent_id=db_comment.parent_id,
        created_at=datetime.fromisoformat(db_comment.created_at) if isinstance(db_comment.created_at, str) else db_comment.created_at,
        updated_at=datetime.fromisoformat(db_comment.updated_at) if isinstance(db_comment.updated_at, str) else db_comment.updated_at,
        replies=[]
    )

@router.post("/{story_id}/bookmark")
async def toggle_bookmark(
    story_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """북마크(즐겨찾기) 토글"""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    # 기존 북마크 확인
    existing_bookmark = db.query(StoryBookmark).filter(
        and_(StoryBookmark.user_id == current_user.id, StoryBookmark.story_id == story_id)
    ).first()
    
    if existing_bookmark:
        # 북마크 취소
        db.delete(existing_bookmark)
        is_bookmarked = False
    else:
        # 북마크 추가
        new_bookmark = StoryBookmark(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            story_id=story_id,
            created_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        db.add(new_bookmark)
        is_bookmarked = True
    
    db.commit()
    
    return {
        "is_bookmarked": is_bookmarked,
        "message": "저장되었습니다." if is_bookmarked else "저장이 취소되었습니다."
    }



@router.get("/bookmarks/me", response_model=StoryListResponse)
async def get_my_bookmarks(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """내 북마크(즐겨찾기) 목록 조회"""
    # 북마크한 스토리 ID 몇찾기
    bookmarked_story_ids = db.query(StoryBookmark.story_id).filter(
        StoryBookmark.user_id == current_user.id
    ).subquery()
    
    # 북마크한 스토리 조회
    query = db.query(Story).filter(
        and_(
            Story.id.in_(bookmarked_story_ids),
            Story.is_active == True
        )
    ).order_by(desc(Story.created_at))
    
    # 전체 개수
    total = query.count()
    
    # 페이지네이션
    offset = (page - 1) * limit
    stories_db = query.offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    stories = []
    for story in stories_db:
        # 작성자 정보
        author = db.query(User).filter(User.id == story.user_id).first()
        
        # 지역 정보
        region_name = None
        if story.region_id1 and story.region_id2:
            region_name = f"{story.region_id1} {story.region_id2}"
        
        # 좋아요 여부
        like = db.query(StoryLike).filter(
            and_(StoryLike.user_id == current_user.id, StoryLike.story_id == story.id)
        ).first()
        is_liked = like is not None
        
        # 댓글 수
        comments_count = db.query(StoryComment).filter(StoryComment.story_id == story.id).count()
        
        stories.append(StoryResponse(
            id=story.id,
            user_id=story.user_id,
            guide_id=story.guide_id,
            title=story.title,
            content=story.content,
            media_type=story.media_type,
            media_url=story.media_url,
            thumbnail_url=story.thumbnail_url,
            category=story.category,
            region_id=story.region_id1,
            view_count=story.view_count,
            like_count=story.like_count,
            is_active=story.is_active,
            created_at=datetime.fromisoformat(story.created_at) if isinstance(story.created_at, str) else story.created_at,
            updated_at=datetime.fromisoformat(story.updated_at) if isinstance(story.updated_at, str) else story.updated_at,
            author_nickname=author.nickname if author else "Unknown",
            author_profile_image=author.profile_image if author else None,
            region_name=region_name,
            is_liked=is_liked,
            comments_count=comments_count,
            is_bookmarked=True  # 북마크 목록이므로 항상 True
        ))
    
    return StoryListResponse(
        stories=stories,
        total=total,
        page=page,
        limit=limit
    )

@router.get("/test-media")
async def test_media():
    """디버깅용 - 현재 등록된 미디어 확인"""
    import os
    stories_path = "uploads/stories"
    thumbnails_path = "uploads/thumbnails"
    
    stories_files = os.listdir(stories_path) if os.path.exists(stories_path) else []
    thumbnails_files = os.listdir(thumbnails_path) if os.path.exists(thumbnails_path) else []
    
    return {
        "stories_count": len(stories_files),
        "thumbnails_count": len(thumbnails_files),
        "stories_files": stories_files[:10],  # 처음 10개만
        "thumbnails_files": thumbnails_files[:10]  # 처음 10개만
    }

@router.post("/request", response_model=dict)
async def create_story_request(
    text: str = Form(...),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """스토리 생성 요청 (AI 생성을 위한 텍스트, 이미지, 음성 전송)"""
    # 임시로 요청 받은 데이터 저장
    request_id = str(uuid.uuid4())
    request_dir = os.path.join("uploads", "requests", request_id)
    os.makedirs(request_dir, exist_ok=True)
    
    # 텍스트 저장
    with open(os.path.join(request_dir, "text.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    
    # 이미지 저장
    image_path = None
    if image:
        image_ext = os.path.splitext(image.filename)[1].lower()
        if image_ext not in [".jpg", ".jpeg", ".png", ".gif"]:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        image_path = os.path.join(request_dir, f"image{image_ext}")
        with open(image_path, "wb") as f:
            content = await image.read()
            f.write(content)
    
    # 오디오 저장
    audio_path = None
    if audio:
        audio_ext = os.path.splitext(audio.filename)[1].lower()
        if audio_ext not in [".mp3", ".wav", ".m4a", ".ogg"]:
            raise HTTPException(status_code=400, detail="Invalid audio format")
        
        audio_path = os.path.join(request_dir, f"audio{audio_ext}")
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
    
    # TODO: AI 처리 큐에 추가 (비동기 처리)
    # 현재는 요청만 받고 저장
    
    return {
        "request_id": request_id,
        "message": "스토리 생성 요청이 접수되었습니다. AI가 스토리를 생성하면 알려드리겠습니다.",
        "user_id": current_user.id,
        "has_image": image is not None,
        "has_audio": audio is not None
    }

@router.post("/upload/", response_model=dict)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """미디어 파일 업로드 (가이드만 가능)"""
    # 가이드 권한 확인
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if not guide or not guide.is_approved:
        raise HTTPException(status_code=403, detail="Only approved guides can upload media")
    
    # 파일 확장자 확인
    allowed_extensions = {
        "video": [".mp4", ".avi", ".mov", ".wmv", ".mkv"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp"],
        "pdf": [".pdf"],
        "audio": [".mp3", ".wav", ".ogg"]
    }
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    media_type = None
    
    for type_name, extensions in allowed_extensions.items():
        if file_ext in extensions:
            media_type = type_name
            break
    
    if not media_type:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # 파일 저장
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # 썸네일 생성
    thumbnail_url = None
    
    if media_type == "video":
        # 비디오 썸네일 생성 (1초 지점의 프레임 추출)
        thumbnail_path = await thumbnail_service.generate_video_thumbnail(
            video_path=file_path,
            time_seconds=1.0,
            size=(720, 1280)  # 9:16 비율
        )
        if thumbnail_path:
            # 썸네일 파일명만 추출
            thumbnail_filename = os.path.basename(thumbnail_path)
            thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"
            print(f"비디오 썸네일 생성 성공: {thumbnail_url}")
        else:
            print(f"비디오 썸네일 생성 실패: {file_path}")
    
    elif media_type == "image":
        # 이미지 썸네일 생성
        thumbnail_path = await thumbnail_service.generate_image_thumbnail(
            image_path=file_path,
            size=(720, 1280)  # 9:16 비율
        )
        if thumbnail_path:
            thumbnail_filename = os.path.basename(thumbnail_path)
            thumbnail_url = f"/uploads/thumbnails/{thumbnail_filename}"
            print(f"이미지 썸네일 생성 성공: {thumbnail_url}")
        else:
            # 이미지의 경우 썸네일 생성 실패 시 원본 사용
            thumbnail_url = f"/uploads/stories/{filename}"
            print(f"이미지 썸네일 생성 실패, 원본 사용: {thumbnail_url}")
    
    # 반환 URL 형식 통일 (/uploads/... 형태로 반환)
    media_url = f"/uploads/stories/{filename}"
    
    return {
        "media_type": media_type,
        "media_url": media_url,
        "thumbnail_url": thumbnail_url
    }

@router.post("/{story_id}/view")
async def increment_view_count(
    story_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """스토리 조회수 증가"""
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.is_active == True
    ).first()
    
    if not story:
        raise HTTPException(
            status_code=404,
            detail="Story not found"
        )
    
    # 조회수 증가
    story.view_count += 1
    db.commit()
    
    return {
        "success": True,
        "view_count": story.view_count
    }

@router.post("/{story_id}/report")
async def report_story(
    story_id: str,
    report_data: StoryReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """스토리 신고"""
    from app.models.report import StoryReport
    
    # 로그에 요청 데이터 출력
    print(f"Report request - story_id: {story_id}, reason: {report_data.reason}, description: {report_data.description}")
    print(f"Reporter: {current_user.id}")
    
    # 스토리 확인
    story = db.query(Story).filter(
        Story.id == story_id,
        Story.is_active == True
    ).first()
    
    if not story:
        raise HTTPException(
            status_code=404,
            detail="Story not found"
        )
    
    # 본인 스토리는 신고할 수 없음
    if story.user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot report your own story"
        )
    
    # 이미 신고한 스토리인지 확인
    existing_report = db.query(StoryReport).filter(
        StoryReport.story_id == story_id,
        StoryReport.reporter_id == current_user.id
    ).first()
    
    if existing_report:
        raise HTTPException(
            status_code=400,
            detail="You have already reported this story"
        )
    
    # 신고 생성
    report = StoryReport(
        story_id=story_id,
        reporter_id=current_user.id,
        reason=report_data.reason,
        description=report_data.description
    )
    
    db.add(report)
    db.commit()
    
    return {
        "success": True,
        "message": "Report submitted successfully"
    }

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.schemas.user import User, UserUpdate
from app.schemas.story import StoryResponse, StoryListResponse
from app.models.user import User as UserModel
from app.models.guide import Guide
from app.models.story import Story, StoryLike
from app.models.matching import MatchingRequest
from app.core.security import get_current_user
from app.core.database import get_db

router = APIRouter()

@router.get("/profile", response_model=User)
async def get_profile(current_user: UserModel = Depends(get_current_user)):
    """현재 사용자 프로필 조회"""
    return User(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        profile_image=current_user.profile_image,
        created_at=current_user.created_at
    )

@router.patch("/profile", response_model=User)
async def update_profile(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 프로필 업데이트"""
    if user_update.nickname:
        current_user.nickname = user_update.nickname
    if user_update.profile_image is not None:
        current_user.profile_image = user_update.profile_image
    
    db.commit()
    db.refresh(current_user)
    
    return User(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        profile_image=current_user.profile_image,
        created_at=current_user.created_at
    )

@router.post("/apply-guide")
async def apply_for_guide(
    bio: dict,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """가이드 신청"""
    # 이미 가이드인지 확인
    existing_guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if existing_guide:
        raise HTTPException(status_code=400, detail="Already applied as guide")
    
    # 새 가이드 생성
    guide = Guide(
        user_id=current_user.id,
        bio=bio.get('bio', ''),
        is_approved=False,
        rating=0.0,
        total_reviews=0
    )
    
    db.add(guide)
    db.commit()
    db.refresh(guide)
    
    return {
        "id": guide.id,
        "user_id": guide.user_id,
        "bio": guide.bio,
        "is_approved": guide.is_approved,
        "rating": float(guide.rating),
        "total_reviews": guide.total_reviews,
        "created_at": guide.created_at
    }

@router.get("/guide-status", response_model=dict)
async def get_guide_status(
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """가이드 상태 확인"""
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    
    if not guide:
        return {"is_guide": False, "is_approved": False}
    
    return {
        "is_guide": True,
        "is_approved": guide.is_approved,
        "guide": {
            "id": guide.id,
            "user_id": guide.user_id,
            "bio": guide.bio,
            "rating": float(guide.rating) if guide.rating else 0.0,
            "total_reviews": guide.total_reviews if guide.total_reviews else 0,
            "is_approved": guide.is_approved,
            "created_at": guide.created_at
        }
    }

@router.get("/{user_id}/guide")
async def get_user_guide(
    user_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """특정 사용자의 가이드 정보 조회"""
    from app.schemas.matching import GuideResponse
    
    # 사용자 확인
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 가이드 정보 조회
    guide = db.query(Guide).filter(Guide.user_id == user_id).first()
    if not guide:
        # 404 대신 null 반환하여 클라이언트가 처리할 수 있도록 함
        return None
    
    return GuideResponse(
        id=guide.id,
        user_id=guide.user_id,
        bio=guide.bio,
        rating=float(guide.rating),
        total_reviews=guide.total_reviews,
        is_approved=guide.is_approved,
        created_at=guide.created_at,
        nickname=user.nickname,
        profile_image=user.profile_image
    )

@router.get("/liked-stories", response_model=StoryListResponse)
async def get_liked_stories(
    page: int = 1,
    limit: int = 20,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """좋아요한 스토리 목록"""
    from datetime import datetime
    from app.models.region import Region
    from app.models.story import StoryComment
    
    # 좋아요한 스토리 ID 목록
    liked_story_ids = db.query(StoryLike.story_id).filter(
        StoryLike.user_id == current_user.id
    ).subquery()
    
    # 스토리 조회
    query = db.query(Story).filter(
        Story.id.in_(liked_story_ids),
        Story.is_active == True
    ).order_by(Story.created_at.desc())
    
    total = query.count()
    offset = (page - 1) * limit
    stories_db = query.offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    stories = []
    for story in stories_db:
        author = db.query(UserModel).filter(UserModel.id == story.user_id).first()
        region = None
        if story.region_id:
            region = db.query(Region).filter(Region.id == story.region_id).first()
        
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
            region_id=story.region_id,
            view_count=story.view_count,
            like_count=story.like_count,
            is_active=story.is_active,
            created_at=datetime.fromisoformat(story.created_at) if isinstance(story.created_at, str) else story.created_at,
            updated_at=datetime.fromisoformat(story.updated_at) if isinstance(story.updated_at, str) else story.updated_at,
            author_nickname=author.nickname if author else "Unknown",
            author_profile_image=author.profile_image if author else None,
            region_name=f"{region.city} {region.district or ''}".strip() if region else None,
            is_liked=True,  # 이미 좋아요한 스토리만 조회하므로
            comments_count=comments_count
        ))
    
    return StoryListResponse(
        stories=stories,
        total=total,
        page=page,
        limit=limit
    )

@router.get("/my-stories", response_model=StoryListResponse)
async def get_my_stories(
    page: int = 1,
    limit: int = 20,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """내가 작성한 스토리 목록 (가이드만)"""
    from datetime import datetime
    from app.models.region import Region
    from app.models.story import StoryComment
    
    # 가이드 확인
    guide = db.query(Guide).filter(Guide.user_id == current_user.id).first()
    if not guide:
        return StoryListResponse(stories=[], total=0, page=page, limit=limit)
    
    # 내 스토리 조회
    query = db.query(Story).filter(
        Story.guide_id == guide.id
    ).order_by(Story.created_at.desc())
    
    total = query.count()
    offset = (page - 1) * limit
    stories_db = query.offset(offset).limit(limit).all()
    
    # 응답 데이터 구성
    stories = []
    for story in stories_db:
        region = None
        if story.region_id:
            region = db.query(Region).filter(Region.id == story.region_id).first()
        
        # 좋아요 여부
        like = db.query(StoryLike).filter(
            StoryLike.user_id == current_user.id,
            StoryLike.story_id == story.id
        ).first()
        
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
            region_id=story.region_id,
            view_count=story.view_count,
            like_count=story.like_count,
            is_active=story.is_active,
            created_at=datetime.fromisoformat(story.created_at) if isinstance(story.created_at, str) else story.created_at,
            updated_at=datetime.fromisoformat(story.updated_at) if isinstance(story.updated_at, str) else story.updated_at,
            author_nickname=current_user.nickname,
            author_profile_image=current_user.profile_image,
            region_name=f"{region.city} {region.district or ''}".strip() if region else None,
            is_liked=like is not None,
            comments_count=comments_count
        ))
    
    return StoryListResponse(
        stories=stories,
        total=total,
        page=page,
        limit=limit
    )

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_, and_
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.models.region import Region
from app.models.story import Story
from app.schemas.region import RegionResponse, RegionListResponse, RegionMapData

router = APIRouter()

@router.get("/", response_model=RegionListResponse)
async def get_regions(
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """지역 목록 조회"""
    query = db.query(Region)
    
    # 검색
    if search:
        query = query.filter(
            or_(
                Region.city.contains(search),
                Region.district.contains(search),
                Region.region_name.contains(search)
            )
        )
    
    # 스토리 수가 많은 순으로 정렬
    query = query.order_by(desc(Region.story_count), Region.city, Region.district)
    
    regions = query.all()
    total = len(regions)
    
    return RegionListResponse(
        regions=[
            RegionResponse(
                id=region.id,
                region_name=region.region_name,
                city=region.city,
                district=region.district,
                latitude=float(region.latitude) if region.latitude else None,
                longitude=float(region.longitude) if region.longitude else None,
                story_count=region.story_count,
                created_at=datetime.fromisoformat(region.created_at) if isinstance(region.created_at, str) else region.created_at
            ) for region in regions
        ],
        total=total
    )

@router.get("/map", response_model=List[RegionMapData])
async def get_map_data(db: Session = Depends(get_db)):
    """지도용 지역 데이터 조회"""
    regions = db.query(Region).filter(
        and_(Region.latitude != None, Region.longitude != None)
    ).all()
    
    map_data = []
    for region in regions:
        # 해당 지역의 인기 카테고리 조회
        popular_categories = db.query(
            Story.category,
            func.count(Story.id).label('count')
        ).filter(
            and_(Story.region_id == region.id, Story.category != None)
        ).group_by(Story.category).order_by(desc('count')).limit(3).all()
        
        map_data.append(RegionMapData(
            id=region.id,
            city=region.city,
            district=region.district,
            latitude=float(region.latitude),
            longitude=float(region.longitude),
            story_count=region.story_count,
            popular_categories=[cat[0] for cat in popular_categories]
        ))
    
    return map_data

@router.get("/{region_id}", response_model=RegionResponse)
async def get_region(
    region_id: str,
    db: Session = Depends(get_db)
):
    """지역 상세 조회"""
    region = db.query(Region).filter(Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    
    return RegionResponse(
        id=region.id,
        region_name=region.region_name,
        city=region.city,
        district=region.district,
        latitude=float(region.latitude) if region.latitude else None,
        longitude=float(region.longitude) if region.longitude else None,
        story_count=region.story_count,
        created_at=datetime.fromisoformat(region.created_at) if isinstance(region.created_at, str) else region.created_at
    )

@router.get("/search-by-name", response_model=List[RegionResponse])
async def search_regions_by_name(
    city: str,
    district: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """시/구 이름으로 지역 검색"""
    query = db.query(Region)
    
    # 도 단위 매핑
    city_mapping = {
        "서울": "서울특별시",
        "부산": "부산광역시",
        "제주": "제주특별자치도",
        "인천": "인천광역시",
        "대구": "대구광역시",
        "대전": "대전광역시",
        "광주": "광주광역시",
        "울산": "울산광역시",
        "세종": "세종특별자치시"
    }
    
    # 시 이름 변환
    mapped_city = city_mapping.get(city, city)
    
    # 상세 지역 매핑을 위한 테이블 (TODO: 확장 필요)
    if mapped_city == city and not mapped_city.endswith("시") and not mapped_city.endswith("도"):
        # 시/군 단위 처리
        query = query.filter(
            or_(
                Region.city.contains(city),
                Region.district == city
            )
        )
    else:
        query = query.filter(Region.city == mapped_city)
    
    if district:
        query = query.filter(Region.district == district)
    
    regions = query.all()
    
    return [
        RegionResponse(
            id=region.id,
            region_name=region.region_name,
            city=region.city,
            district=region.district,
            latitude=float(region.latitude) if region.latitude else None,
            longitude=float(region.longitude) if region.longitude else None,
            story_count=region.story_count,
            created_at=datetime.fromisoformat(region.created_at) if isinstance(region.created_at, str) else region.created_at
        ) for region in regions
    ]

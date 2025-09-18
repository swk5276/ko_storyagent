"""
지역 데이터 초기화 스크립트
새로운 지역 구조에 맞게 regions 테이블을 초기화합니다.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.region import Region
from app.core.region_data import REGION_DATA
import uuid

def init_regions():
    """지역 데이터 초기화"""
    db = SessionLocal()
    
    try:
        # 기존 데이터 삭제
        print("기존 지역 데이터 삭제 중...")
        db.query(Region).delete()
        db.commit()
        print("기존 데이터 삭제 완료")
        
        # 새로운 지역 데이터 추가
        print("새로운 지역 데이터 추가 중...")
        
        for category, cities in REGION_DATA.items():
            for city in cities:
                region = Region(
                    id=str(uuid.uuid4()),
                    region_name=f"{category} - {city}",
                    city=category,  # 큰 카테고리를 city로 사용
                    district=city,  # 실제 도시명을 district로 사용
                    story_count=0
                )
                db.add(region)
                print(f"추가: {category} - {city}")
        
        db.commit()
        print(f"총 {db.query(Region).count()}개의 지역 데이터 추가 완료")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_regions()

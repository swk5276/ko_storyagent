import httpx
from typing import Optional, Dict, Any

class KakaoService:
    KAKAO_API_BASE = "https://kapi.kakao.com"
    
    @staticmethod
    async def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
        """카카오 액세스 토큰으로 사용자 정보 가져오기"""
        print(f"카카오 사용자 정보 요청 - 토큰: {access_token[:20]}...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{KakaoService.KAKAO_API_BASE}/v2/user/me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                print(f"카카오 API 응답: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"카카오 사용자 데이터: {data}")
                    return {
                        "kakao_id": str(data["id"]),
                        "email": data.get("kakao_account", {}).get("email"),
                        "nickname": data.get("properties", {}).get("nickname", f"사용자{data['id']}"),
                        "profile_image": data.get("properties", {}).get("profile_image")
                    }
                else:
                    print(f"카카오 API 에러 응답: {response.text}")
                return None
            except Exception as e:
                print(f"카카오 API 오류: {e}")
                return None

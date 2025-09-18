# Story Book 프로덕션 환경 설정

## MySQL 데이터베이스 테이블 생성

```sql
-- users 테이블
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    kakao_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    nickname VARCHAR(100) NOT NULL,
    profile_image VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kakao_id (kakao_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- refresh_tokens 테이블
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## 카카오 개발자 설정

1. [카카오 개발자 사이트](https://developers.kakao.com/)에서 애플리케이션 생성
2. 플랫폼 설정:
   - Android: 패키지명 등록
   - iOS: 번들 ID 등록
3. 카카오 로그인 활성화
4. Redirect URI 설정: `kakao{NATIVE_APP_KEY}://oauth`

## FastAPI 서버 설정

### 1. 환경 변수 설정 (.env 파일)
```env
# Database
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-mysql-user
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=storybook

# JWT (반드시 변경)
SECRET_KEY=your-very-long-random-secret-key-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kakao
KAKAO_REST_API_KEY=your-kakao-rest-api-key

# CORS (프로덕션 도메인으로 변경)
BACKEND_CORS_ORIGINS=["https://your-domain.com"]
```

### 2. 서버 실행
```bash
cd C:\app\stroy_book_server
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Flutter 앱 설정

### 1. 카카오 SDK 초기화
`lib/main.dart`:
```dart
KakaoSdk.init(nativeAppKey: 'YOUR_NATIVE_APP_KEY');
```

### 2. API 서버 URL 변경
`lib/constants/api_constants.dart`:
```dart
static const String baseUrl = 'https://your-api-domain.com/api/v1';
```

### 3. Android 설정
`android/app/src/main/AndroidManifest.xml`:
```xml
<data android:host="oauth" android:scheme="kakao{YOUR_NATIVE_APP_KEY}" />
```

## 프로덕션 체크리스트

- [ ] SECRET_KEY를 안전한 랜덤 값으로 변경
- [ ] CORS 설정을 실제 도메인으로 제한
- [ ] HTTPS 인증서 설정
- [ ] 데이터베이스 백업 설정
- [ ] 로그 수집 시스템 구축
- [ ] 에러 모니터링 시스템 구축
- [ ] API Rate Limiting 설정
- [ ] 카카오 앱 프로덕션 승인 받기

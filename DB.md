# Story Book Database Schema

## Database Information
- **Database Type**: PostgreSQL
- **Database Name**: storybook
- **Character Set**: UTF8
- **Collation**: en_US.utf8

## Tables

### 1. users (사용자)
사용자 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 사용자 고유 ID |
| kakao_id | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | 카카오 로그인 ID |
| email | VARCHAR(255) | NULL | 이메일 주소 |
| nickname | VARCHAR(100) | NOT NULL | 사용자 닉네임 |
| profile_image | VARCHAR(500) | NULL | 프로필 이미지 URL |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 수정 시간 |

### 2. refresh_tokens (리프레시 토큰)
JWT 리프레시 토큰 관리 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 토큰 ID |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) ON DELETE CASCADE | 사용자 ID |
| token | VARCHAR(500) | UNIQUE, NOT NULL, INDEX | 리프레시 토큰 |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL | 만료 시간 |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | 생성 시간 |

### 3. regions (지역)
지역 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 지역 ID |
| region_name | VARCHAR(100) | NOT NULL | 지역명 (예: 서울특별시 강남구) |
| city | VARCHAR(50) | NOT NULL | 시/도 |
| district | VARCHAR(50) | NULL | 구/군 |
| latitude | DECIMAL(10, 8) | NULL | 위도 |
| longitude | DECIMAL(11, 8) | NULL | 경도 |
| story_count | INTEGER | DEFAULT 0 | 해당 지역의 스토리 수 |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |

### 4. guides (가이드)
가이드 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 가이드 ID |
| user_id | VARCHAR(36) | UNIQUE, NOT NULL, FOREIGN KEY (users.id) ON DELETE CASCADE | 사용자 ID |
| bio | TEXT | NULL | 가이드 소개 |
| rating | DECIMAL(3, 2) | DEFAULT 0.00 | 평균 평점 (0.00 ~ 5.00) |
| total_reviews | INTEGER | DEFAULT 0 | 총 리뷰 수 |
| is_approved | BOOLEAN | DEFAULT FALSE | 승인 여부 |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 수정 시간 |

### 5. stories (스토리)
스토리(게시물) 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 스토리 ID |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 작성자 ID |
| guide_id | VARCHAR(36) | NULL, FOREIGN KEY (guides.id) | 가이드 ID (가이드가 작성한 경우) |
| region_id | VARCHAR(36) | NULL, FOREIGN KEY (regions.id) | 지역 ID |
| title | VARCHAR(255) | NOT NULL | 제목 |
| content | TEXT | NULL | 내용 |
| media_type | ENUM('video', 'image', 'pdf', 'audio') | NOT NULL | 미디어 타입 |
| media_url | VARCHAR(500) | NOT NULL | 미디어 파일 URL |
| thumbnail_url | VARCHAR(500) | NULL | 썸네일 이미지 URL |
| category | VARCHAR(50) | NULL | 카테고리 |
| view_count | INTEGER | DEFAULT 0 | 조회수 |
| like_count | INTEGER | DEFAULT 0 | 좋아요 수 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성화 여부 |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 수정 시간 |

### 6. story_likes (스토리 좋아요)
스토리 좋아요 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 좋아요 ID |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 사용자 ID |
| story_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (stories.id) | 스토리 ID |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |

**Unique Constraint**: (user_id, story_id) - 한 사용자가 같은 스토리에 중복 좋아요 방지

### 7. story_comments (스토리 댓글)
스토리 댓글 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 댓글 ID |
| story_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (stories.id) | 스토리 ID |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 작성자 ID |
| content | TEXT | NOT NULL | 댓글 내용 |
| parent_id | VARCHAR(36) | NULL, FOREIGN KEY (story_comments.id) | 부모 댓글 ID (대댓글) |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 수정 시간 |

### 8. matching_requests (매칭 요청)
가이드 매칭 요청 정보를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 매칭 요청 ID |
| user_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 요청자 ID |
| guide_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (guides.id) | 가이드 ID |
| story_id | VARCHAR(36) | NULL, FOREIGN KEY (stories.id) | 관련 스토리 ID |
| matching_type | ENUM('online_chat', 'guide_tour', 'home_visit') | NOT NULL | 매칭 타입 |
| status | ENUM('pending', 'accepted', 'rejected', 'completed', 'cancelled') | DEFAULT 'pending' | 매칭 상태 |
| requested_date | DATE | NOT NULL | 요청 날짜 |
| requested_time | TIME | NULL | 요청 시간 |
| message | TEXT | NULL | 요청 메시지 |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 수정 시간 |

### 9. chat_messages (채팅 메시지)
매칭된 사용자 간 채팅 메시지를 저장하는 테이블

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID 형식의 메시지 ID |
| matching_request_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (matching_requests.id) | 매칭 요청 ID |
| sender_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 발신자 ID |
| receiver_id | VARCHAR(36) | NOT NULL, FOREIGN KEY (users.id) | 수신자 ID |
| message | TEXT | NOT NULL | 메시지 내용 |
| is_read | BOOLEAN | DEFAULT FALSE | 읽음 여부 |
| created_at | VARCHAR(19) | NOT NULL, DEFAULT NOW() | 생성 시간 |

## Indexes
- users.kakao_id
- refresh_tokens.token
- story_likes(user_id, story_id) - Composite Unique Index
- stories.user_id
- stories.guide_id
- stories.region_id
- story_comments.story_id
- story_comments.user_id
- story_comments.parent_id
- matching_requests.user_id
- matching_requests.guide_id
- chat_messages.matching_request_id
- chat_messages.sender_id
- chat_messages.receiver_id

## Foreign Key Constraints
1. refresh_tokens.user_id → users.id (ON DELETE CASCADE)
2. guides.user_id → users.id (ON DELETE CASCADE)
3. stories.user_id → users.id
4. stories.guide_id → guides.id
5. stories.region_id → regions.id
6. story_likes.user_id → users.id
7. story_likes.story_id → stories.id
8. story_comments.story_id → stories.id
9. story_comments.user_id → users.id
10. story_comments.parent_id → story_comments.id
11. matching_requests.user_id → users.id
12. matching_requests.guide_id → guides.id
13. matching_requests.story_id → stories.id
14. chat_messages.matching_request_id → matching_requests.id
15. chat_messages.sender_id → users.id
16. chat_messages.receiver_id → users.id

## Notes
- 모든 테이블의 ID는 UUID v4 형식 사용
- 시간 관련 필드는 TIMESTAMP WITH TIME ZONE 또는 VARCHAR(19) 형식 사용
- 파일 URL은 최대 500자까지 저장 가능
- story_likes 테이블은 (user_id, story_id) 조합으로 unique constraint 설정 필요

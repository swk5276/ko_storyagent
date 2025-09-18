-- StoryBook 데이터베이스 복원 스크립트
-- 생성일: 2025-01-24
-- 설명: MySQL 데이터베이스 완전 복원

-- 1. 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS storybook CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE storybook;

-- 2. users 테이블
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    kakao_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    nickname VARCHAR(100) NOT NULL,
    profile_image VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kakao_id (kakao_id)
);

-- 3. refresh_tokens 테이블
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token (token)
);

-- 4. regions 테이블
CREATE TABLE IF NOT EXISTS regions (
    id VARCHAR(36) PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    story_count INT DEFAULT 0,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'))
);

-- 5. guides 테이블
CREATE TABLE IF NOT EXISTS guides (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    bio TEXT,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    total_reviews INT DEFAULT 0,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    updated_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 6. stories 테이블
CREATE TABLE IF NOT EXISTS stories (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    guide_id VARCHAR(36),
    region_id1 VARCHAR(50),
    region_id2 VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    content TEXT,
    media_type ENUM('video', 'image', 'pdf', 'audio') NOT NULL,
    media_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    category VARCHAR(50),
    view_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    updated_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (guide_id) REFERENCES guides(id),
    INDEX idx_user_id (user_id),
    INDEX idx_guide_id (guide_id)
);

-- 7. story_likes 테이블
CREATE TABLE IF NOT EXISTS story_likes (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    story_id VARCHAR(36) NOT NULL,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    UNIQUE KEY unique_user_story (user_id, story_id)
);

-- 8. story_comments 테이블
CREATE TABLE IF NOT EXISTS story_comments (
    id VARCHAR(36) PRIMARY KEY,
    story_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    parent_id VARCHAR(36),
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    updated_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_id) REFERENCES story_comments(id),
    INDEX idx_story_id (story_id),
    INDEX idx_user_id (user_id)
);

-- 9. story_bookmarks 테이블
CREATE TABLE IF NOT EXISTS story_bookmarks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    story_id VARCHAR(36) NOT NULL,
    created_at VARCHAR(19) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_story_bookmark (user_id, story_id)
);

-- 10. matching_requests 테이블
CREATE TABLE IF NOT EXISTS matching_requests (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    guide_id VARCHAR(36) NOT NULL,
    story_id VARCHAR(36),
    matching_type ENUM('online_chat', 'guide_tour', 'home_visit') NOT NULL,
    status ENUM('pending', 'accepted', 'rejected', 'completed', 'cancelled') DEFAULT 'pending',
    requested_date DATE NOT NULL,
    requested_time TIME,
    message TEXT,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    updated_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (guide_id) REFERENCES guides(id),
    FOREIGN KEY (story_id) REFERENCES stories(id),
    INDEX idx_user_id (user_id),
    INDEX idx_guide_id (guide_id)
);

-- 11. chat_rooms 테이블
CREATE TABLE IF NOT EXISTS chat_rooms (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    guide_id VARCHAR(36) NOT NULL,
    matching_request_id VARCHAR(36),
    last_message TEXT,
    last_message_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (guide_id) REFERENCES users(id),
    FOREIGN KEY (matching_request_id) REFERENCES matching_requests(id)
);

-- 12. chat_messages 테이블
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    chat_room_id VARCHAR(36),
    matching_request_id VARCHAR(36) NOT NULL,
    sender_id VARCHAR(36) NOT NULL,
    receiver_id VARCHAR(36) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at VARCHAR(19) DEFAULT (DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s')),
    FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id),
    FOREIGN KEY (matching_request_id) REFERENCES matching_requests(id),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id),
    INDEX idx_matching_request_id (matching_request_id),
    INDEX idx_sender_id (sender_id),
    INDEX idx_receiver_id (receiver_id)
);

-- 13. story_reports 테이블
CREATE TABLE IF NOT EXISTS story_reports (
    id VARCHAR(36) PRIMARY KEY,
    story_id VARCHAR(36) NOT NULL,
    reporter_id VARCHAR(36) NOT NULL,
    reason VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (story_id) REFERENCES stories(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);

-- 14. 지역 데이터 삽입
-- 수도권
INSERT INTO regions (id, region_name, city, district, story_count) VALUES
(UUID(), '수도권 - 서울', '수도권', '서울', 0),
(UUID(), '수도권 - 인천', '수도권', '인천', 0),
(UUID(), '수도권 - 수원', '수도권', '수원', 0),
(UUID(), '수도권 - 성남', '수도권', '성남', 0),
(UUID(), '수도권 - 의정부', '수도권', '의정부', 0),
(UUID(), '수도권 - 안양', '수도권', '안양', 0),
(UUID(), '수도권 - 부천', '수도권', '부천', 0),
(UUID(), '수도권 - 광명', '수도권', '광명', 0),
(UUID(), '수도권 - 평택', '수도권', '평택', 0),
(UUID(), '수도권 - 동두천', '수도권', '동두천', 0),
(UUID(), '수도권 - 안산', '수도권', '안산', 0),
(UUID(), '수도권 - 고양', '수도권', '고양', 0),
(UUID(), '수도권 - 과천', '수도권', '과천', 0),
(UUID(), '수도권 - 구리', '수도권', '구리', 0),
(UUID(), '수도권 - 남양주', '수도권', '남양주', 0),
(UUID(), '수도권 - 오산', '수도권', '오산', 0),
(UUID(), '수도권 - 시흥', '수도권', '시흥', 0),
(UUID(), '수도권 - 군포', '수도권', '군포', 0),
(UUID(), '수도권 - 의왕', '수도권', '의왕', 0),
(UUID(), '수도권 - 하남', '수도권', '하남', 0),
(UUID(), '수도권 - 용인', '수도권', '용인', 0),
(UUID(), '수도권 - 파주', '수도권', '파주', 0),
(UUID(), '수도권 - 이천', '수도권', '이천', 0),
(UUID(), '수도권 - 안성', '수도권', '안성', 0),
(UUID(), '수도권 - 김포', '수도권', '김포', 0),
(UUID(), '수도권 - 화성', '수도권', '화성', 0),
(UUID(), '수도권 - 광주', '수도권', '광주', 0),
(UUID(), '수도권 - 양주', '수도권', '양주', 0),
(UUID(), '수도권 - 포천', '수도권', '포천', 0),
(UUID(), '수도권 - 여주', '수도권', '여주', 0),
(UUID(), '수도권 - 연천', '수도권', '연천', 0),
(UUID(), '수도권 - 가평', '수도권', '가평', 0),
(UUID(), '수도권 - 양평', '수도권', '양평', 0);

-- 강원
INSERT INTO regions (id, region_name, city, district, story_count) VALUES
(UUID(), '강원 - 춘천', '강원', '춘천', 0),
(UUID(), '강원 - 원주', '강원', '원주', 0),
(UUID(), '강원 - 강릉', '강원', '강릉', 0),
(UUID(), '강원 - 동해', '강원', '동해', 0),
(UUID(), '강원 - 태백', '강원', '태백', 0),
(UUID(), '강원 - 속초', '강원', '속초', 0),
(UUID(), '강원 - 삼척', '강원', '삼척', 0),
(UUID(), '강원 - 홍천', '강원', '홍천', 0),
(UUID(), '강원 - 횡성', '강원', '횡성', 0),
(UUID(), '강원 - 영월', '강원', '영월', 0),
(UUID(), '강원 - 평창', '강원', '평창', 0),
(UUID(), '강원 - 정선', '강원', '정선', 0),
(UUID(), '강원 - 철원', '강원', '철원', 0),
(UUID(), '강원 - 화천', '강원', '화천', 0),
(UUID(), '강원 - 양구', '강원', '양구', 0),
(UUID(), '강원 - 인제', '강원', '인제', 0),
(UUID(), '강원 - 고성', '강원', '고성', 0),
(UUID(), '강원 - 양양', '강원', '양양', 0);

-- 충청
INSERT INTO regions (id, region_name, city, district, story_count) VALUES
(UUID(), '충청 - 대전', '충청', '대전', 0),
(UUID(), '충청 - 세종', '충청', '세종', 0),
(UUID(), '충청 - 청주', '충청', '청주', 0),
(UUID(), '충청 - 충주', '충청', '충주', 0),
(UUID(), '충청 - 제천', '충청', '제천', 0),
(UUID(), '충청 - 보은', '충청', '보은', 0),
(UUID(), '충청 - 옥천', '충청', '옥천', 0),
(UUID(), '충청 - 영동', '충청', '영동', 0),
(UUID(), '충청 - 증평', '충청', '증평', 0),
(UUID(), '충청 - 진천', '충청', '진천', 0),
(UUID(), '충청 - 괴산', '충청', '괴산', 0),
(UUID(), '충청 - 음성', '충청', '음성', 0),
(UUID(), '충청 - 단양', '충청', '단양', 0),
(UUID(), '충청 - 천안', '충청', '천안', 0),
(UUID(), '충청 - 공주', '충청', '공주', 0),
(UUID(), '충청 - 보령', '충청', '보령', 0),
(UUID(), '충청 - 아산', '충청', '아산', 0),
(UUID(), '충청 - 서산', '충청', '서산', 0),
(UUID(), '충청 - 논산', '충청', '논산', 0),
(UUID(), '충청 - 계룡', '충청', '계룡', 0),
(UUID(), '충청 - 당진', '충청', '당진', 0),
(UUID(), '충청 - 금산', '충청', '금산', 0),
(UUID(), '충청 - 부여', '충청', '부여', 0),
(UUID(), '충청 - 서천', '충청', '서천', 0),
(UUID(), '충청 - 청양', '충청', '청양', 0),
(UUID(), '충청 - 홍성', '충청', '홍성', 0),
(UUID(), '충청 - 예산', '충청', '예산', 0),
(UUID(), '충청 - 태안', '충청', '태안', 0);

-- 전라
INSERT INTO regions (id, region_name, city, district, story_count) VALUES
(UUID(), '전라 - 광주', '전라', '광주', 0),
(UUID(), '전라 - 제주', '전라', '제주', 0),
(UUID(), '전라 - 전주', '전라', '전주', 0),
(UUID(), '전라 - 익산', '전라', '익산', 0),
(UUID(), '전라 - 군산', '전라', '군산', 0),
(UUID(), '전라 - 정읍', '전라', '정읍', 0),
(UUID(), '전라 - 남원', '전라', '남원', 0),
(UUID(), '전라 - 김제', '전라', '김제', 0),
(UUID(), '전라 - 무주', '전라', '무주', 0),
(UUID(), '전라 - 완주', '전라', '완주', 0),
(UUID(), '전라 - 부안', '전라', '부안', 0),
(UUID(), '전라 - 고창', '전라', '고창', 0),
(UUID(), '전라 - 임실', '전라', '임실', 0),
(UUID(), '전라 - 순창', '전라', '순창', 0),
(UUID(), '전라 - 진안', '전라', '진안', 0),
(UUID(), '전라 - 장수', '전라', '장수', 0),
(UUID(), '전라 - 목포', '전라', '목포', 0),
(UUID(), '전라 - 여수', '전라', '여수', 0),
(UUID(), '전라 - 순천', '전라', '순천', 0),
(UUID(), '전라 - 나주', '전라', '나주', 0),
(UUID(), '전라 - 광양', '전라', '광양', 0),
(UUID(), '전라 - 담양', '전라', '담양', 0),
(UUID(), '전라 - 곡성', '전라', '곡성', 0),
(UUID(), '전라 - 구례', '전라', '구례', 0),
(UUID(), '전라 - 고흥', '전라', '고흥', 0),
(UUID(), '전라 - 보성', '전라', '보성', 0),
(UUID(), '전라 - 화순', '전라', '화순', 0),
(UUID(), '전라 - 장흥', '전라', '장흥', 0),
(UUID(), '전라 - 강진', '전라', '강진', 0),
(UUID(), '전라 - 해남', '전라', '해남', 0),
(UUID(), '전라 - 영암', '전라', '영암', 0),
(UUID(), '전라 - 무안', '전라', '무안', 0),
(UUID(), '전라 - 함평', '전라', '함평', 0),
(UUID(), '전라 - 영광', '전라', '영광', 0),
(UUID(), '전라 - 장성', '전라', '장성', 0),
(UUID(), '전라 - 완도', '전라', '완도', 0),
(UUID(), '전라 - 진도', '전라', '진도', 0),
(UUID(), '전라 - 신안', '전라', '신안', 0);

-- 경상
INSERT INTO regions (id, region_name, city, district, story_count) VALUES
(UUID(), '경상 - 부산', '경상', '부산', 0),
(UUID(), '경상 - 울산', '경상', '울산', 0),
(UUID(), '경상 - 대구', '경상', '대구', 0),
(UUID(), '경상 - 포항', '경상', '포항', 0),
(UUID(), '경상 - 경주', '경상', '경주', 0),
(UUID(), '경상 - 김천', '경상', '김천', 0),
(UUID(), '경상 - 안동', '경상', '안동', 0),
(UUID(), '경상 - 구미', '경상', '구미', 0),
(UUID(), '경상 - 영주', '경상', '영주', 0),
(UUID(), '경상 - 영천', '경상', '영천', 0),
(UUID(), '경상 - 상주', '경상', '상주', 0),
(UUID(), '경상 - 문경', '경상', '문경', 0),
(UUID(), '경상 - 경산', '경상', '경산', 0),
(UUID(), '경상 - 의성', '경상', '의성', 0),
(UUID(), '경상 - 청송', '경상', '청송', 0),
(UUID(), '경상 - 영양', '경상', '영양', 0),
(UUID(), '경상 - 영덕', '경상', '영덕', 0),
(UUID(), '경상 - 청도', '경상', '청도', 0),
(UUID(), '경상 - 고령', '경상', '고령', 0),
(UUID(), '경상 - 성주', '경상', '성주', 0),
(UUID(), '경상 - 칠곡', '경상', '칠곡', 0),
(UUID(), '경상 - 예천', '경상', '예천', 0),
(UUID(), '경상 - 봉화', '경상', '봉화', 0),
(UUID(), '경상 - 울진', '경상', '울진', 0),
(UUID(), '경상 - 울릉', '경상', '울릉', 0),
(UUID(), '경상 - 창원', '경상', '창원', 0),
(UUID(), '경상 - 진주', '경상', '진주', 0),
(UUID(), '경상 - 통영', '경상', '통영', 0),
(UUID(), '경상 - 사천', '경상', '사천', 0),
(UUID(), '경상 - 김해', '경상', '김해', 0),
(UUID(), '경상 - 밀양', '경상', '밀양', 0),
(UUID(), '경상 - 거제', '경상', '거제', 0),
(UUID(), '경상 - 양산', '경상', '양산', 0),
(UUID(), '경상 - 의령', '경상', '의령', 0),
(UUID(), '경상 - 함안', '경상', '함안', 0),
(UUID(), '경상 - 창녕', '경상', '창녕', 0),
(UUID(), '경상 - 고성', '경상', '고성', 0),
(UUID(), '경상 - 남해', '경상', '남해', 0),
(UUID(), '경상 - 하동', '경상', '하동', 0),
(UUID(), '경상 - 산청', '경상', '산청', 0),
(UUID(), '경상 - 함양', '경상', '함양', 0),
(UUID(), '경상 - 거창', '경상', '거창', 0),
(UUID(), '경상 - 합천', '경상', '합천', 0);

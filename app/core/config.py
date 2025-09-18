from pydantic_settings import BaseSettings
import secrets

class Settings(BaseSettings):
    # Database
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "storybook"
    
    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Kakao
    KAKAO_REST_API_KEY: str = ""
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080", "http://10.0.2.2:8000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

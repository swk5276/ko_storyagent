from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from urllib.parse import quote_plus

# 비밀번호를 URL 인코딩
encoded_password = quote_plus(settings.MYSQL_PASSWORD)

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{settings.MYSQL_USER}:{encoded_password}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

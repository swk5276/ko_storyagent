#!/bin/bash

# 데이터베이스 초기화 스크립트

echo "Initializing database..."

# Alembic 초기 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 실행
alembic upgrade head

echo "Database initialization completed!"

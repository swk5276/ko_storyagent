# Story Book Server - Azure Deployment Manual

## 사전 요구사항
1. Azure CLI 설치
2. Docker Desktop 설치
3. Azure 구독 활성화
4. PowerShell 또는 Bash 터미널

## 로컬 테스트

### Docker Compose로 로컬 테스트
```bash
# Docker Compose로 로컬 환경 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# API 테스트
curl http://localhost:8005/health
```

### 로컬 Docker 이미지 빌드
```bash
# Docker 이미지 빌드
docker build -t storybook-api:latest .

# 컨테이너 실행
docker run -d -p 8005:8005 --name storybook-api \
  -e DATABASE_URL="postgresql://user:password@host.docker.internal:5432/storybook" \
  storybook-api:latest
```

## Azure 배포 가이드

### 1. Azure CLI 로그인
```bash
az login
```

### 2. 자동 배포 스크립트 실행
PowerShell에서 실행:
```powershell
# 스크립트 실행 권한 부여
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 배포 스크립트 실행
.\deploy-azure.ps1
```

### 3. 수동 배포 (선택사항)

#### 3.1 리소스 그룹 생성
```bash
az group create --name storybook-rg --location koreacentral
```

#### 3.2 Azure Container Registry 생성
```bash
az acr create --resource-group storybook-rg --name storybookacr --sku Basic --admin-enabled true
```

#### 3.3 PostgreSQL 데이터베이스 생성
```bash
# PostgreSQL 서버 생성
az postgres server create \
    --resource-group storybook-rg \
    --name storybook-db-server \
    --location koreacentral \
    --admin-user storybookadmin \
    --admin-password YourSecurePassword123! \
    --sku-name B_Gen5_1 \
    --version 11

# 방화벽 규칙 추가
az postgres server firewall-rule create \
    --resource-group storybook-rg \
    --server storybook-db-server \
    --name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 0.0.0.0

# 데이터베이스 생성
az postgres db create \
    --resource-group storybook-rg \
    --server-name storybook-db-server \
    --name storybook
```

#### 3.4 Docker 이미지 빌드 및 푸시
```bash
# ACR 로그인
az acr login --name storybookacr

# 이미지 빌드 및 푸시
az acr build --registry storybookacr --image storybook-api:latest .
```

#### 3.5 App Service 생성 및 배포
```bash
# App Service Plan 생성
az appservice plan create \
    --name storybook-plan \
    --resource-group storybook-rg \
    --sku B1 \
    --is-linux

# Web App 생성
az webapp create \
    --resource-group storybook-rg \
    --plan storybook-plan \
    --name storybook-api \
    --deployment-container-image-name storybookacr.azurecr.io/storybook-api:latest

# ACR 자격 증명 설정
az webapp config container set \
    --name storybook-api \
    --resource-group storybook-rg \
    --docker-custom-image-name storybookacr.azurecr.io/storybook-api:latest \
    --docker-registry-server-url https://storybookacr.azurecr.io
```

### 4. 환경 변수 설정
```bash
az webapp config appsettings set \
    --resource-group storybook-rg \
    --name storybook-api \
    --settings \
        DATABASE_URL="postgresql://storybookadmin@storybook-db-server:YourSecurePassword123!@storybook-db-server.postgres.database.azure.com:5432/storybook?sslmode=require" \
        SECRET_KEY="your-production-secret-key" \
        ALGORITHM="HS256" \
        ACCESS_TOKEN_EXPIRE_MINUTES="30" \
        BACKEND_CORS_ORIGINS='["https://your-frontend-domain.com"]'
```

### 5. 데이터베이스 마이그레이션
```bash
# SSH로 컨테이너 접속
az webapp ssh --name storybook-api --resource-group storybook-rg

# 컨테이너 내부에서 실행
python -m alembic upgrade head
```

## 배포 확인

### API Health Check
```bash
curl https://storybook-api.azurewebsites.net/health
```

### 로그 확인
```bash
az webapp log tail --name storybook-api --resource-group storybook-rg
```

## CI/CD 설정 (GitHub Actions)

`.github/workflows/azure-deploy.yml` 파일 생성:

```yaml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Login to ACR
      uses: azure/docker-login@v1
      with:
        login-server: storybookacr.azurecr.io
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}
    
    - name: Build and push Docker image
      run: |
        docker build . -t storybookacr.azurecr.io/storybook-api:latest
        docker push storybookacr.azurecr.io/storybook-api:latest
    
    - name: Deploy to Azure Web App
      uses: azure/webapps-deploy@v2
      with:
        app-name: storybook-api
        images: storybookacr.azurecr.io/storybook-api:latest
```

## 모니터링 및 유지보수

### Application Insights 설정
```bash
az monitor app-insights component create \
    --app storybook-api-insights \
    --location koreacentral \
    --resource-group storybook-rg \
    --application-type web
```

### 자동 스케일링 설정
```bash
az monitor autoscale create \
    --resource-group storybook-rg \
    --resource storybook-plan \
    --resource-type Microsoft.Web/serverfarms \
    --name autoscale-storybook \
    --min-count 1 \
    --max-count 5 \
    --count 1
```

## 보안 권장사항

1. **SSL/TLS 인증서 설정**
   - Azure App Service에서 무료 SSL 인증서 사용
   - 사용자 지정 도메인 설정

2. **환경 변수 보안**
   - Azure Key Vault 사용 고려
   - 민감한 정보는 절대 코드에 포함하지 않기

3. **네트워크 보안**
   - VNet 통합 고려
   - Private Endpoint 사용

4. **백업 설정**
   - PostgreSQL 자동 백업 활성화
   - 백업 보존 기간 설정 (기본 7일)

## 문제 해결

### 1. 컨테이너가 시작되지 않는 경우
```bash
# 로그 확인
az webapp log download --name storybook-api --resource-group storybook-rg

# 환경 변수 확인
az webapp config appsettings list --name storybook-api --resource-group storybook-rg
```

### 2. 데이터베이스 연결 오류
- PostgreSQL 방화벽 규칙 확인
- DATABASE_URL 형식 확인
- SSL 모드 설정 확인

### 3. 파일 업로드 문제
- Azure Storage Account 연결 확인
- CORS 설정 확인
- 컨테이너 권한 확인

## 비용 최적화

1. **개발/테스트 환경**
   - B1 App Service Plan 사용
   - Basic PostgreSQL SKU 사용
   - 야간/주말 자동 종료 설정

2. **프로덕션 환경**
   - S1 이상 App Service Plan 권장
   - General Purpose PostgreSQL SKU
   - Reserved Instance 구매 고려

## 추가 리소스

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/azure/postgresql/)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

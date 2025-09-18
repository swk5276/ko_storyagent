# Azure Container Registry 및 App Service 배포 스크립트

# 변수 설정
$RESOURCE_GROUP = "storybook-rg"
$LOCATION = "koreacentral"
$ACR_NAME = "storybookacr"
$APP_SERVICE_PLAN = "storybook-plan"
$WEB_APP_NAME = "storybook-api"
$POSTGRES_SERVER = "storybook-db-server"
$DB_NAME = "storybook"
$DB_USER = "storybookadmin"
$DB_PASSWORD = "YourSecurePassword123!"

# 1. 리소스 그룹 생성
az group create --name $RESOURCE_GROUP --location $LOCATION

# 2. Azure Container Registry 생성
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# 3. PostgreSQL 서버 생성
az postgres server create `
    --resource-group $RESOURCE_GROUP `
    --name $POSTGRES_SERVER `
    --location $LOCATION `
    --admin-user $DB_USER `
    --admin-password $DB_PASSWORD `
    --sku-name B_Gen5_1 `
    --version 11

# 4. PostgreSQL 방화벽 규칙 추가 (Azure 서비스 허용)
az postgres server firewall-rule create `
    --resource-group $RESOURCE_GROUP `
    --server $POSTGRES_SERVER `
    --name AllowAzureServices `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 0.0.0.0

# 5. 데이터베이스 생성
az postgres db create `
    --resource-group $RESOURCE_GROUP `
    --server-name $POSTGRES_SERVER `
    --name $DB_NAME

# 6. App Service Plan 생성
az appservice plan create `
    --name $APP_SERVICE_PLAN `
    --resource-group $RESOURCE_GROUP `
    --sku B1 `
    --is-linux

# 7. Docker 이미지 빌드 및 푸시
az acr build --registry $ACR_NAME --image storybook-api:latest .

# 8. Web App 생성
az webapp create `
    --resource-group $RESOURCE_GROUP `
    --plan $APP_SERVICE_PLAN `
    --name $WEB_APP_NAME `
    --deployment-container-image-name "$ACR_NAME.azurecr.io/storybook-api:latest"

# 9. ACR 자격 증명 가져오기
$ACR_USERNAME = az acr credential show --name $ACR_NAME --query username -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv

# 10. Web App 컨테이너 설정
az webapp config container set `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP `
    --docker-custom-image-name "$ACR_NAME.azurecr.io/storybook-api:latest" `
    --docker-registry-server-url "https://$ACR_NAME.azurecr.io" `
    --docker-registry-server-user $ACR_USERNAME `
    --docker-registry-server-password $ACR_PASSWORD

# 11. 환경 변수 설정
az webapp config appsettings set `
    --resource-group $RESOURCE_GROUP `
    --name $WEB_APP_NAME `
    --settings `
        DATABASE_URL="postgresql://${DB_USER}@${POSTGRES_SERVER}:${DB_PASSWORD}@${POSTGRES_SERVER}.postgres.database.azure.com:5432/${DB_NAME}?sslmode=require" `
        SECRET_KEY="your-production-secret-key" `
        ALGORITHM="HS256" `
        ACCESS_TOKEN_EXPIRE_MINUTES="30" `
        BACKEND_CORS_ORIGINS='["https://your-frontend-domain.com"]'

# 12. 연속 배포 활성화
az webapp deployment container config `
    --enable-cd true `
    --name $WEB_APP_NAME `
    --resource-group $RESOURCE_GROUP

Write-Host "Deployment completed!"
Write-Host "API URL: https://$WEB_APP_NAME.azurewebsites.net"

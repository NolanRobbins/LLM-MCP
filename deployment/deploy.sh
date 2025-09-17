#!/bin/bash
set -e

# Load environment variables
source ../setup/set_env.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploying AI Gateway MCP Server to Cloud Run${NC}"

# Validate required environment variables
if [ -z "$GOOGLE_CLOUD_PROJECT" ] || [ -z "$GOOGLE_CLOUD_LOCATION" ]; then
    echo -e "${RED}❌ Error: Missing required environment variables${NC}"
    echo "Please set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION in set_env.sh"
    exit 1
fi

# Set deployment variables
SERVICE_NAME="ai-gateway-mcp-server"
REGION="${GOOGLE_CLOUD_LOCATION}"
PROJECT="${GOOGLE_CLOUD_PROJECT}"

echo -e "${YELLOW}📦 Building and deploying to Cloud Run...${NC}"

# Deploy to Cloud Run with authentication required
gcloud run deploy ${SERVICE_NAME} \
    --no-allow-unauthenticated \
    --region=${REGION} \
    --project=${PROJECT} \
    --source=. \
    --service-account="ai-gateway-service@${PROJECT}.iam.gserviceaccount.com" \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT},GOOGLE_CLOUD_LOCATION=${REGION}" \
    --set-secrets="OPENAI_API_KEY=openai-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,GOOGLE_API_KEY=google-api-key:latest,XAI_API_KEY=xai-api-key:latest" \
    --cpu=2 \
    --memory=4Gi \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=900 \
    --concurrency=10 \
    --labels=app=ai-gateway-mcp,version=v1

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT} \
    --format='value(status.url)')

echo -e "${GREEN}✅ Deployment successful!${NC}"
echo -e "Service URL: ${SERVICE_URL}"

# Grant invoker permissions to the current user
USER_EMAIL=$(gcloud config get-value account)
echo -e "${YELLOW}🔐 Granting Cloud Run Invoker permissions to ${USER_EMAIL}...${NC}"

gcloud projects add-iam-policy-binding ${PROJECT} \
    --member=user:${USER_EMAIL} \
    --role='roles/run.invoker'

echo -e "${GREEN}✅ Permissions granted${NC}"

# Instructions for testing
echo -e "\n${GREEN}📝 Next Steps:${NC}"
echo "1. Test locally with proxy:"
echo "   gcloud run services proxy ${SERVICE_NAME} --region=${REGION} --port=8080"
echo ""
echo "2. In another terminal, run:"
echo "   python test_server.py"
echo ""
echo "3. For ADK Agent integration, see adk_agent/README.md"

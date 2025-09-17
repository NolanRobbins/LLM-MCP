#!/bin/bash
# Enable required APIs for AI Gateway MCP Server
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load environment variables
if [ -f "set_env.sh" ]; then
    source set_env.sh
else
    echo -e "${RED}❌ Error: set_env.sh not found${NC}"
    exit 1
fi

echo -e "${GREEN}🔧 Enabling APIs for AI Gateway MCP Server${NC}"

# Check if project is set
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo -e "${RED}❌ Error: GOOGLE_CLOUD_PROJECT not set${NC}"
    echo "Please run ./create_project.sh first"
    exit 1
fi

echo -e "${BLUE}📋 Project: ${GOOGLE_CLOUD_PROJECT}${NC}"

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudresourcemanager.googleapis.com \
    --project=$GOOGLE_CLOUD_PROJECT

# Set default region
gcloud config set run/region us-central1

# Create service account for Cloud Run
echo -e "${YELLOW}👤 Creating service account...${NC}"
gcloud iam service-accounts create ai-gateway-service \
    --description="Service account for AI Gateway MCP Server" \
    --display-name="AI Gateway Service Account" \
    --project=$GOOGLE_CLOUD_PROJECT

# Grant necessary roles to service account
SERVICE_ACCOUNT_EMAIL="ai-gateway-service@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"

echo -e "${YELLOW}🔐 Granting IAM roles...${NC}"
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.logWriter"

echo -e "${GREEN}✅ APIs and service account setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Service Account: ${SERVICE_ACCOUNT_EMAIL}${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Add your API keys to set_env.sh"
echo "2. Run: ./setup_secrets.sh"
echo "3. Run: ./deploy.sh"
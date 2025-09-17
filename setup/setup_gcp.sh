#!/bin/bash
# Google Cloud Setup Script for AI Gateway MCP Server
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌍 Setting up Google Cloud for AI Gateway MCP Server${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: Google Cloud CLI not found${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    echo "Or on macOS: brew install --cask google-cloud-sdk"
    exit 1
fi

# Authenticate with Google Cloud
echo -e "${YELLOW}🔐 Authenticating with Google Cloud...${NC}"
gcloud auth login
gcloud auth application-default login

# Set default project (you can change this)
PROJECT_ID="ai-gateway-mcp-$(date +%s)"
echo -e "${BLUE}📋 Creating project: ${PROJECT_ID}${NC}"

# Create project
gcloud projects create $PROJECT_ID --name="AI Gateway MCP Server"

# Set as default project
gcloud config set project $PROJECT_ID

# Enable billing (you'll need to link a billing account manually)
echo -e "${YELLOW}💳 Please link a billing account in the Google Cloud Console${NC}"
echo "Visit: https://console.cloud.google.com/billing/projects"

# Enable required APIs
echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    cloudresourcemanager.googleapis.com

# Set default region
gcloud config set run/region us-central1

# Create service account for Cloud Run
echo -e "${YELLOW}👤 Creating service account...${NC}"
gcloud iam service-accounts create ai-gateway-service \
    --description="Service account for AI Gateway MCP Server" \
    --display-name="AI Gateway Service Account"

# Grant necessary roles to service account
SERVICE_ACCOUNT_EMAIL="ai-gateway-service@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "${YELLOW}🔐 Granting IAM roles...${NC}"
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/monitoring.metricWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/logging.logWriter"

# Update set_env.sh with project details
echo -e "${YELLOW}📝 Updating environment configuration...${NC}"
sed -i '' "s/your-project-id/${PROJECT_ID}/g" set_env.sh

echo -e "${GREEN}✅ Google Cloud setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Project Details:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: us-central1"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Link a billing account at: https://console.cloud.google.com/billing/projects"
echo "2. Add your API keys to Secret Manager: ./setup_secrets.sh"
echo "3. Deploy the service: ./deploy.sh"
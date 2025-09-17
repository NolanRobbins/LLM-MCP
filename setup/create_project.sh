#!/bin/bash
# Create Google Cloud Project for AI Gateway MCP Server
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Creating Google Cloud project for AI Gateway MCP Server${NC}"

# Generate unique project ID
PROJECT_ID="ai-gateway-mcp-$(date +%s)"
echo -e "${BLUE}📋 Project ID: ${PROJECT_ID}${NC}"

# Create project
echo -e "${YELLOW}🔨 Creating project...${NC}"
gcloud projects create $PROJECT_ID --name="AI Gateway MCP Server"

# Set as default project
echo -e "${YELLOW}⚙️ Setting as default project...${NC}"
gcloud config set project $PROJECT_ID

# Enable billing (you'll need to link a billing account manually)
echo -e "${YELLOW}💳 Please link a billing account in the Google Cloud Console${NC}"
echo "Visit: https://console.cloud.google.com/billing/projects"
echo "Project ID: $PROJECT_ID"

# Update set_env.sh with project details
echo -e "${YELLOW}📝 Updating environment configuration...${NC}"
sed -i '' "s/your-project-id/${PROJECT_ID}/g" set_env.sh

echo -e "${GREEN}✅ Project created successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Project Details:${NC}"
echo "Project ID: $PROJECT_ID"
echo "Name: AI Gateway MCP Server"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Link billing account at: https://console.cloud.google.com/billing/projects"
echo "2. Run: ./enable_apis.sh"
echo "3. Add your API keys to set_env.sh"
echo "4. Run: ./setup_secrets.sh"
echo "5. Run: ./deploy.sh"
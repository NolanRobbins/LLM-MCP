# Deployment Scripts

This directory contains scripts for deploying the LLM MCP Gateway to production environments.

## Scripts

### `deploy.sh`
**Purpose**: Deploy to Google Cloud Run
**Usage**: `./deploy.sh`
**Description**: Builds and deploys the AI Gateway MCP Server to Google Cloud Run. Automatically loads environment variables from `../setup/set_env.sh`.

## Prerequisites

Before running deployment scripts:

1. Complete the setup process:
   ```bash
   cd ../setup/
   ./setup_gcp.sh
   ./create_project.sh
   source set_env.sh
   ./enable_apis.sh
   ```

2. Ensure you're authenticated with Google Cloud:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## Deployment Process

1. Deploy to Cloud Run:
   ```bash
   cd deployment/
   ./deploy.sh
   ```

The deployment script will:
- Load environment variables
- Build the Docker container
- Deploy to Google Cloud Run
- Configure environment variables
- Set up proper IAM permissions
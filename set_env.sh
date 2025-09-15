#!/bin/bash
# Environment configuration for AI Gateway MCP Server

# Google Cloud Configuration
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

# AI Provider API Keys - Replace with your actual keys
export OPENAI_API_KEY="your-openai-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GOOGLE_API_KEY="your-google-api-key"
export XAI_API_KEY="your-xai-api-key"

# Server Configuration
export USER_ID="default-user"

# Cache Configuration
export CACHE_TTL_HOURS=24
export SIMILARITY_THRESHOLD=0.95

# Rate Limiting
export DEFAULT_RPM=60
export DEFAULT_RPH=1000
export BURST_LIMIT=10

# Monitoring
export ENABLE_METRICS=true
export LOG_LEVEL=INFO

echo "Environment variables loaded for AI Gateway MCP Server"

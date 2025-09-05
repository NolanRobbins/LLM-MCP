#!/bin/bash
# Environment configuration for AI Gateway MCP Server

# Google Cloud Configuration
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"

# AI Provider API Keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export GOOGLE_API_KEY="your-google-key"
export MISTRAL_API_KEY="your-mistral-key"
export GROQ_API_KEY="your-groq-key"

# Server Configuration
export PORT=8080
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

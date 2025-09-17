# Setup Scripts

This directory contains scripts for setting up the LLM MCP Gateway environment and Google Cloud Platform resources.

## Scripts

### `set_env.sh`
**Purpose**: Environment variable configuration
**Usage**: `source set_env.sh`
**Description**: Sets all required environment variables for the application including API keys, GCP settings, and application configuration.

### `setup_gcp.sh`
**Purpose**: Initial Google Cloud Platform setup
**Usage**: `./setup_gcp.sh`
**Description**: Sets up the Google Cloud environment, installs dependencies, and configures authentication.

### `create_project.sh`
**Purpose**: Creates a new GCP project
**Usage**: `./create_project.sh`
**Description**: Creates a new Google Cloud project with a unique ID for the AI Gateway MCP Server.

### `enable_apis.sh`
**Purpose**: Enables required Google Cloud APIs
**Usage**: `./enable_apis.sh`
**Description**: Enables all necessary Google Cloud APIs required for the AI Gateway MCP Server.

## Setup Order

1. First time setup:
   ```bash
   cd setup/
   ./setup_gcp.sh          # Install gcloud and setup
   ./create_project.sh      # Create GCP project
   source set_env.sh        # Load environment variables
   ./enable_apis.sh         # Enable required APIs
   ```

2. Daily development:
   ```bash
   source setup/set_env.sh  # Load environment variables
   ```
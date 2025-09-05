# ADK Agent Integration

This directory contains the ADK (Agent Development Kit) agent that integrates with the AI Gateway MCP Server.

## Overview

The ADK Agent demonstrates how to use Google's Agent Development Kit with the AI Gateway MCP Server to create intelligent agents that can:

- Route AI requests intelligently across multiple providers
- Use semantic caching to reduce costs
- Optimize prompts for better results
- Monitor provider health and performance

## Setup

1. Install dependencies:
```bash
cd adk_agent
pip install -r requirements.txt
```

2. Make sure the AI Gateway MCP Server is running:
```bash
cd ..
python server.py
```

3. Run the ADK Agent:
```bash
python agent.py
```

## Features

- **Intelligent Routing**: Automatically selects the best AI provider
- **Cost Optimization**: Uses caching and cost tracking
- **Prompt Optimization**: Improves prompts for better results
- **Health Monitoring**: Tracks provider status and performance

## Usage

The agent provides a conversational interface where you can:

- Ask questions that get routed to the best AI provider
- Check provider status and health
- Optimize prompts for better results
- Get cost and performance metrics

## Integration with MCP Server

The agent uses the MCP (Model Context Protocol) to communicate with the AI Gateway server, enabling:

- Tool-based interactions
- Structured data exchange
- Error handling and fallback
- Real-time monitoring

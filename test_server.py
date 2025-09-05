#!/usr/bin/env python3
"""
Test client for the AI Gateway MCP Server
Following the pattern from the Cloud Run MCP workshop
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# For local testing before package installation
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_ai_gateway():
    """Test the AI Gateway MCP Server"""
    
    print("🚀 Testing AI Gateway MCP Server")
    print("=" * 50)
    
    # Determine if testing locally or remote
    server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8080")
    
    async with stdio_client(
        StdioServerParameters(
            command="python",
            args=["server.py"] if "localhost" in server_url else None,
            env=None
        )
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            print("\n📋 Available Tools:")
            tools = await session.list_tools()
            for tool in tools:
                print(f"  - {tool.name}: {tool.description[:50]}...")
            
            # Test 1: Basic completion
            print("\n🧪 Test 1: Basic Completion")
            result = await session.call_tool(
                "unified_completion",
                arguments={
                    "prompt": "What is machine learning in one sentence?",
                    "model": "auto",
                    "max_tokens": 100
                }
            )
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 2: Low latency requirement
            print("\n🧪 Test 2: Low Latency Requirement")
            result = await session.call_tool(
                "unified_completion",
                arguments={
                    "prompt": "Count to 5",
                    "requirements": {"low_latency": True}
                }
            )
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Test 3: Provider status
            print("\n🧪 Test 3: Provider Status")
            result = await session.call_tool("get_provider_status")
            print(f"Providers: {json.dumps(result, indent=2)}")
            
            # Test 4: Prompt optimization
            print("\n🧪 Test 4: Prompt Optimization")
            result = await session.call_tool(
                "optimize_prompt",
                arguments={
                    "prompt": "Tell me about AI",
                    "optimization_goal": "clarity"
                }
            )
            print(f"Optimized: {json.dumps(result, indent=2)}")
            
            # Test 5: Usage metrics
            print("\n🧪 Test 5: Usage Metrics")
            result = await session.call_tool(
                "get_usage_metrics",
                arguments={"time_range": "1h"}
            )
            print(f"Metrics: {json.dumps(result, indent=2)}")
            
            # Test 6: Health check
            print("\n🧪 Test 6: Health Check")
            result = await session.call_tool("health_check")
            print(f"Health: {json.dumps(result, indent=2)}")
            
            print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_ai_gateway())

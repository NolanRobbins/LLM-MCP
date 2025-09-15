#!/usr/bin/env python3
"""
Simple HTTP test for AI Gateway MCP Server
Tests FastMCP endpoints directly
"""
import requests
import json
import subprocess
import sys

def get_auth_token():
    """Get authentication token for Google Cloud"""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ Failed to get authentication token")
        return None

def test_mcp_endpoints():
    """Test MCP server endpoints"""
    base_url = "https://ai-gateway-mcp-server-898076230411.us-central1.run.app"

    # Get auth token
    print("🔐 Getting authentication token...")
    token = get_auth_token()
    if not token:
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("🧪 Testing AI Gateway MCP Server")
    print("=" * 50)

    # Test 1: Root endpoint (should return something about FastMCP)
    print("\n📡 Test 1: Root endpoint")
    try:
        response = requests.get(f"{base_url}/", headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Root test failed: {e}")

    # Test 2: Try MCP specific endpoints
    print("\n📡 Test 2: MCP Health (if exists)")
    try:
        response = requests.get(f"{base_url}/mcp/health", headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ MCP health test failed: {e}")

    # Test 3: Check if server is responding to any requests
    print("\n📡 Test 3: Server connectivity")
    try:
        response = requests.get(f"{base_url}/docs", headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ FastAPI docs endpoint found!")
        print(f"Response preview: {response.text[:200]}...")
    except Exception as e:
        print(f"❌ Docs test failed: {e}")

    # Test 4: Check service logs for any errors
    print("\n📋 Test 4: Checking recent logs...")
    try:
        result = subprocess.run([
            "gcloud", "run", "services", "logs", "read", "ai-gateway-mcp-server",
            "--project=ai-gateway-mcp-1757874286",
            "--region=us-central1",
            "--limit=5"
        ], capture_output=True, text=True, check=True)

        print("Recent logs:")
        print(result.stdout[-500:])  # Last 500 chars

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get logs: {e}")

    print("\n✅ Connectivity tests completed!")
    return True

if __name__ == "__main__":
    print("🚀 Testing AI Gateway MCP Server Connectivity")
    print("This tests basic connectivity and server health")
    print("-" * 60)

    success = test_mcp_endpoints()

    if success:
        print("\n🎉 Basic connectivity tests completed!")
        print("📝 Note: For full MCP testing, use the Claude Code MCP inspector")
    else:
        print("\n💥 Some tests failed. Check the output above for details.")
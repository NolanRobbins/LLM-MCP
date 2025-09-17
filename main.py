#!/usr/bin/env python3
"""
Entry point for LLM MCP Gateway Server
"""

if __name__ == "__main__":
    from src.llm_mcp.server.server import main
    main()
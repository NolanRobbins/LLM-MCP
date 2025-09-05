"""
ADK Agent that uses the AI Gateway MCP Server
Demonstrates integration with Google's Agent Development Kit
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from google.adk import Agent
from google.adk.tools import Tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class AIGatewayAgent:
    """ADK Agent that integrates with AI Gateway MCP Server"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8080"):
        self.mcp_server_url = mcp_server_url
        self.agent = Agent(
            name="AI Gateway Agent",
            description="Agent that uses AI Gateway for intelligent AI routing"
        )
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools for the agent"""
        
        @self.agent.tool()
        async def ask_ai(prompt: str, requirements: Optional[Dict[str, Any]] = None) -> str:
            """
            Ask AI a question using the intelligent gateway
            
            Args:
                prompt: The question or prompt
                requirements: Optional requirements like low_latency, high_quality
                
            Returns:
                AI response
            """
            try:
                async with stdio_client(
                    StdioServerParameters(
                        command="python",
                        args=["server.py"],
                        env=None
                    )
                ) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "unified_completion",
                            arguments={
                                "prompt": prompt,
                                "requirements": requirements or {}
                            }
                        )
                        
                        if "error" in result:
                            return f"Error: {result['error']}"
                        
                        return result.get("text", "No response")
                        
            except Exception as e:
                logger.error(f"Error calling AI Gateway: {e}")
                return f"Error: {str(e)}"
        
        @self.agent.tool()
        async def get_provider_status() -> str:
            """Get status of all AI providers"""
            try:
                async with stdio_client(
                    StdioServerParameters(
                        command="python",
                        args=["server.py"],
                        env=None
                    )
                ) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool("get_provider_status")
                        return f"Provider status: {result}"
                        
            except Exception as e:
                logger.error(f"Error getting provider status: {e}")
                return f"Error: {str(e)}"
        
        @self.agent.tool()
        async def optimize_prompt(prompt: str, goal: str = "clarity") -> str:
            """Optimize a prompt for better results"""
            try:
                async with stdio_client(
                    StdioServerParameters(
                        command="python",
                        args=["server.py"],
                        env=None
                    )
                ) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        
                        result = await session.call_tool(
                            "optimize_prompt",
                            arguments={
                                "prompt": prompt,
                                "optimization_goal": goal
                            }
                        )
                        
                        return f"Optimized prompt: {result.get('optimized', 'Error')}"
                        
            except Exception as e:
                logger.error(f"Error optimizing prompt: {e}")
                return f"Error: {str(e)}"
    
    async def run(self, user_input: str) -> str:
        """Run the agent with user input"""
        try:
            response = await self.agent.run(user_input)
            return response
        except Exception as e:
            logger.error(f"Agent error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

async def main():
    """Main function to run the ADK Agent"""
    agent = AIGatewayAgent()
    
    print("🤖 AI Gateway ADK Agent")
    print("Type 'quit' to exit")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Goodbye!")
                break
            
            response = await agent.run(user_input)
            print(f"Agent: {response}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

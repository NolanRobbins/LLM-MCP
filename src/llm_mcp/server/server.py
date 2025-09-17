"""
AI Gateway MCP Server - Secure, Production-Ready Multi-Provider Gateway
Following the pattern from the Cloud Run MCP deployment lab
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from dotenv import load_dotenv

from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Import gateway modules
from ..gateway.router import IntelligentRouter
from ..gateway.cache import SemanticCache
from ..gateway.rate_limiter import AdaptiveRateLimiter
from ..gateway.cost_tracker import CostOptimizer
from ..gateway.metrics import MetricsCollector

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize MCP server with metadata
mcp = FastMCP(
    "AI Gateway MCP Server"
)

# Initialize gateway components
router = IntelligentRouter()
cache = SemanticCache()
rate_limiter = AdaptiveRateLimiter()
cost_optimizer = CostOptimizer()
metrics = MetricsCollector()

# Data models for better type safety
class CompletionRequest(BaseModel):
    """Request model for AI completions"""
    prompt: str
    model: Optional[str] = Field(default="auto", description="Model selection or 'auto' for intelligent routing")
    max_tokens: Optional[int] = Field(default=1000, ge=1, le=32000)
    temperature: Optional[float] = Field(default=0.7, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)
    stream: Optional[bool] = Field(default=True)
    cache_enabled: Optional[bool] = Field(default=True)
    requirements: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProviderStatus(BaseModel):
    """Health status of a provider"""
    name: str
    status: str
    latency_ms: float
    success_rate: float
    available: bool

# MCP Tools Implementation

@mcp.prompt()
def ai_gateway_prompt() -> str:
    """System prompt for the AI Gateway"""
    return """You are an AI Gateway assistant that helps users interact with multiple AI providers.
    
    You can:
    1. Route requests intelligently to the best provider based on requirements
    2. Cache responses to reduce costs and latency
    3. Track usage and costs across providers
    4. Handle failover when providers are unavailable
    5. Optimize prompts for better results
    
    Available providers: OpenAI, Anthropic, Google, xAI Grok
    
    When users ask questions, use the unified_completion tool to get AI responses.
    You can specify requirements like 'low_latency', 'low_cost', or 'high_quality'.
    """

@mcp.tool()
async def unified_completion(
    prompt: str,
    model: str = "auto",
    max_tokens: int = 1000,
    temperature: float = 0.7,
    requirements: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Send a completion request through the AI Gateway with intelligent routing.
    
    Args:
        prompt: The input prompt
        model: Specific model or "auto" for intelligent selection
        max_tokens: Maximum tokens in response
        temperature: Creativity parameter (0-2)
        requirements: Optional requirements like {"low_latency": true, "low_cost": true}
    
    Returns:
        Response with text, model used, cost, and metrics
    """
    try:
        # Check rate limits
        user_id = os.getenv("USER_ID", "default")
        if rate_limiter.should_throttle(user_id):
            return {
                "error": "Rate limit exceeded",
                "retry_after": rate_limiter.get_retry_after(user_id)
            }
        
        # Check cache if enabled
        if requirements and requirements.get("cache_enabled", True):
            cached = await cache.find_similar(prompt, threshold=0.95)
            if cached:
                logger.info(f"Cache hit for prompt: {prompt[:50]}...")
                metrics.record_cache_hit()
                return {
                    "text": cached["text"],
                    "model": cached["model"],
                    "cached": True,
                    "cost": 0,
                    "latency_ms": cached.get("latency_ms", 0)
                }
        
        # Route to optimal provider
        provider = await router.route_request(prompt, model, requirements or {})
        logger.info(f"Routing to provider: {provider['name']} with model: {provider['model']}")
        
        # Make the actual API call (simplified for example)
        start_time = datetime.now()
        response = await provider["client"].complete(
            prompt=prompt,
            model=provider["model"],
            max_tokens=max_tokens,
            temperature=temperature
        )
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Calculate cost
        cost = cost_optimizer.calculate_cost(
            provider=provider["name"],
            model=provider["model"],
            input_tokens=len(prompt.split()),  # Simplified tokenization
            output_tokens=len(response["text"].split())
        )
        
        # Update metrics
        metrics.record_request(
            provider=provider["name"],
            model=provider["model"],
            latency_ms=latency_ms,
            cost=cost,
            success=True
        )
        
        # Cache the response
        if requirements and requirements.get("cache_enabled", True):
            await cache.store(prompt, response["text"], provider["model"], latency_ms)
        
        return {
            "text": response["text"],
            "model": provider["model"],
            "provider": provider["name"],
            "cached": False,
            "cost": cost,
            "latency_ms": latency_ms,
            "tokens_used": {
                "input": len(prompt.split()),
                "output": len(response["text"].split())
            }
        }
        
    except Exception as e:
        logger.error(f"Error in unified_completion: {str(e)}")
        metrics.record_request(
            provider=model,
            model=model,
            latency_ms=0,
            cost=0,
            success=False
        )
        
        # Attempt failover
        if requirements and requirements.get("failover_enabled", True):
            return await _failover_completion(prompt, max_tokens, temperature, requirements)
        
        return {"error": str(e)}

@mcp.tool()
async def get_provider_status() -> List[ProviderStatus]:
    """
    Get the current status of all AI providers.
    
    Returns:
        List of provider statuses with availability and performance metrics
    """
    statuses = []
    for provider_name in router.get_providers():
        health = await router.check_provider_health(provider_name)
        statuses.append(ProviderStatus(
            name=provider_name,
            status=health["status"],
            latency_ms=health["latency_ms"],
            success_rate=health["success_rate"],
            available=health["available"]
        ))
    return statuses

@mcp.tool()
async def get_usage_metrics(
    time_range: str = "1h",
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get usage metrics and costs for the gateway.
    
    Args:
        time_range: Time range (1h, 24h, 7d, 30d)
        provider: Optional filter by provider
    
    Returns:
        Usage statistics including requests, costs, and performance metrics
    """
    return await metrics.get_metrics(time_range, provider)

@mcp.tool()
async def optimize_prompt(
    prompt: str,
    optimization_goal: str = "clarity"
) -> Dict[str, str]:
    """
    Optimize a prompt for better AI responses.
    
    Args:
        prompt: Original prompt
        optimization_goal: Goal (clarity, brevity, specificity, creativity)
    
    Returns:
        Optimized prompt with explanation
    """
    optimizer_prompt = f"""
    Optimize this prompt for {optimization_goal}:
    
    Original: {prompt}
    
    Provide:
    1. Optimized version
    2. Key changes made
    3. Expected improvement
    """
    
    # Use a fast model for optimization
    response = await unified_completion(
        prompt=optimizer_prompt,
        model="o4-mini",
        max_tokens=500,
        temperature=0.3,
        requirements={"low_cost": True}
    )
    
    return {
        "original": prompt,
        "optimized": response["text"],
        "goal": optimization_goal
    }

@mcp.tool()
async def run_ab_test(
    prompt_a: str,
    prompt_b: str,
    test_model: str = "auto",
    iterations: int = 3
) -> Dict[str, Any]:
    """
    Run A/B test comparing two prompts.
    
    Args:
        prompt_a: First prompt variant
        prompt_b: Second prompt variant
        test_model: Model to test with
        iterations: Number of test iterations
    
    Returns:
        Comparison results with recommendations
    """
    results_a = []
    results_b = []
    
    for i in range(iterations):
        # Test prompt A
        response_a = await unified_completion(
            prompt=prompt_a,
            model=test_model,
            requirements={"cache_enabled": False}
        )
        results_a.append(response_a)
        
        # Test prompt B
        response_b = await unified_completion(
            prompt=prompt_b,
            model=test_model,
            requirements={"cache_enabled": False}
        )
        results_b.append(response_b)
    
    # Calculate averages
    avg_latency_a = sum(r["latency_ms"] for r in results_a) / iterations
    avg_latency_b = sum(r["latency_ms"] for r in results_b) / iterations
    avg_cost_a = sum(r["cost"] for r in results_a) / iterations
    avg_cost_b = sum(r["cost"] for r in results_b) / iterations
    
    return {
        "prompt_a": {
            "text": prompt_a,
            "avg_latency_ms": avg_latency_a,
            "avg_cost": avg_cost_a,
            "responses": [r["text"] for r in results_a]
        },
        "prompt_b": {
            "text": prompt_b,
            "avg_latency_ms": avg_latency_b,
            "avg_cost": avg_cost_b,
            "responses": [r["text"] for r in results_b]
        },
        "recommendation": "A" if avg_latency_a < avg_latency_b and avg_cost_a < avg_cost_b else "B"
    }

async def _failover_completion(prompt, max_tokens, temperature, requirements):
    """Internal failover logic"""
    providers = router.get_available_providers()
    for provider in providers:
        try:
            return await unified_completion(
                prompt=prompt,
                model=provider,
                max_tokens=max_tokens,
                temperature=temperature,
                requirements={**requirements, "failover_enabled": False}
            )
        except Exception as e:
            logger.warning(f"Failover attempt with {provider} failed: {str(e)}")
            continue
    return {"error": "All providers failed"}

# Health check endpoint
@mcp.tool()
async def health_check() -> Dict[str, str]:
    """Check if the gateway is healthy"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run the MCP server
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8080))
    
    logger.info(f"Starting AI Gateway MCP Server on port {port}")
    
    # Start the server with production settings
    uvicorn.run(
        mcp.http_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )

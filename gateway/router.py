"""
Intelligent routing logic for selecting optimal AI provider
Based on requirements, cost, latency, and capabilities - 2025 Latest Models
"""
import asyncio
import random
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelCapabilities:
    """Capabilities and characteristics of a model"""
    name: str
    provider: str
    context_length: int
    supports_functions: bool
    supports_vision: bool
    supports_streaming: bool
    avg_latency_ms: float
    cost_per_1m_tokens: float
    quality_score: float  # 0-1 score
    specialties: List[str]  # e.g., ["code", "reasoning", "creative"]

class IntelligentRouter:
    """Routes requests to optimal AI provider based on multiple factors"""

    def __init__(self):
        self.providers = self._initialize_providers()
        self.health_cache = {}
        self.performance_history = []

    def _initialize_providers(self) -> Dict[str, ModelCapabilities]:
        """Initialize provider configurations with 2025 models"""
        return {
            # OpenAI 2025 Models
            "gpt-5": ModelCapabilities(
                name="gpt-5",
                provider="openai",
                context_length=128000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=750,
                cost_per_1m_tokens=15.00,
                quality_score=0.98,
                specialties=["reasoning", "creative", "analysis", "math", "coding"]
            ),
            "o3": ModelCapabilities(
                name="o3",
                provider="openai",
                context_length=128000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=1200,
                cost_per_1m_tokens=20.00,
                quality_score=0.99,
                specialties=["reasoning", "complex-problem-solving", "math", "coding"]
            ),
            "o4-mini": ModelCapabilities(
                name="o4-mini",
                provider="openai",
                context_length=128000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                avg_latency_ms=400,
                cost_per_1m_tokens=5.00,
                quality_score=0.91,
                specialties=["reasoning", "cost-efficient", "fast-inference"]
            ),

            # Anthropic 2025 Models
            "claude-opus-4.1": ModelCapabilities(
                name="claude-opus-4.1",
                provider="anthropic",
                context_length=1000000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=900,
                cost_per_1m_tokens=75.00,
                quality_score=0.97,
                specialties=["code", "reasoning", "long-form", "agentic-tasks"]
            ),
            "claude-sonnet-4": ModelCapabilities(
                name="claude-sonnet-4",
                provider="anthropic",
                context_length=1000000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=600,
                cost_per_1m_tokens=15.00,
                quality_score=0.94,
                specialties=["code", "reasoning", "balanced", "efficiency"]
            ),

            # Google 2025 Models
            "gemini-2.5-pro": ModelCapabilities(
                name="gemini-2.5-pro",
                provider="google",
                context_length=2000000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=800,
                cost_per_1m_tokens=12.00,
                quality_score=0.96,
                specialties=["thinking", "long-context", "multimodal", "analysis"]
            ),
            "gemini-2.5-flash": ModelCapabilities(
                name="gemini-2.5-flash",
                provider="google",
                context_length=1000000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=500,
                cost_per_1m_tokens=3.00,
                quality_score=0.92,
                specialties=["price-performance", "thinking", "agentic", "speed"]
            ),

            # xAI 2025 Models
            "grok-4": ModelCapabilities(
                name="grok-4",
                provider="xai",
                context_length=256000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=600,
                cost_per_1m_tokens=15.00,
                quality_score=0.95,
                specialties=["reasoning", "real-time", "creative", "web-search"]
            ),
            "grok-4-heavy": ModelCapabilities(
                name="grok-4-heavy",
                provider="xai",
                context_length=256000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=1000,
                cost_per_1m_tokens=25.00,
                quality_score=0.98,
                specialties=["reasoning", "complex-tasks", "real-time", "premium"]
            )
        }

    async def route_request(
        self,
        prompt: str,
        preferred_model: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route request to optimal provider based on requirements

        Args:
            prompt: The input prompt
            preferred_model: User's preferred model or "auto"
            requirements: Requirements like low_latency, low_cost, high_quality

        Returns:
            Selected provider configuration
        """
        # If specific model requested and available, use it
        if preferred_model != "auto" and preferred_model in self.providers:
            return self._create_provider_config(self.providers[preferred_model])

        # Classify the task type
        task_type = self._classify_task(prompt)

        # Score each provider based on requirements
        scores = {}
        for model_name, capabilities in self.providers.items():
            score = await self._score_provider(
                capabilities,
                task_type,
                requirements,
                len(prompt)
            )
            scores[model_name] = score

        # Select the best provider
        best_model = max(scores.keys(), key=lambda k: scores[k])
        logger.info(f"Selected {best_model} with score {scores[best_model]:.2f}")

        return self._create_provider_config(self.providers[best_model])

    def _classify_task(self, prompt: str) -> str:
        """Classify the type of task based on prompt content"""
        prompt_lower = prompt.lower()

        # Enhanced classification for 2025 models
        if any(keyword in prompt_lower for keyword in ["code", "function", "debug", "program", "algorithm"]):
            return "code"
        elif any(keyword in prompt_lower for keyword in ["story", "poem", "creative", "imagine", "write"]):
            return "creative"
        elif any(keyword in prompt_lower for keyword in ["analyze", "explain", "summarize", "reasoning", "think"]):
            return "reasoning"
        elif any(keyword in prompt_lower for keyword in ["math", "calculate", "solve", "equation", "formula"]):
            return "math"
        elif any(keyword in prompt_lower for keyword in ["long", "document", "context", "large"]):
            return "long-context"
        elif any(keyword in prompt_lower for keyword in ["image", "picture", "visual", "see", "photo"]):
            return "multimodal"
        elif any(keyword in prompt_lower for keyword in ["real-time", "current", "latest", "news", "today"]):
            return "real-time"
        else:
            return "general"

    async def _score_provider(
        self,
        capabilities: ModelCapabilities,
        task_type: str,
        requirements: Dict[str, Any],
        prompt_length: int
    ) -> float:
        """Score a provider based on task and requirements"""
        score = 0.0

        # Task specialty bonus
        if task_type in capabilities.specialties:
            score += 20

        # Quality score (if high quality required)
        if requirements.get("high_quality", False):
            score += capabilities.quality_score * 30
        else:
            score += capabilities.quality_score * 10

        # Latency score (if low latency required)
        if requirements.get("low_latency", False):
            latency_score = max(0, 100 - (capabilities.avg_latency_ms / 10))
            score += latency_score * 0.3

        # Cost score (if low cost required)
        if requirements.get("low_cost", False):
            # Invert cost - lower cost gets higher score
            cost_score = max(0, 100 - capabilities.cost_per_1m_tokens)
            score += cost_score * 0.3

        # Context length bonus for long prompts
        if prompt_length > capabilities.context_length * 0.5:  # Using 50% as threshold
            if capabilities.context_length >= 1000000:  # 1M+ tokens
                score += 15  # Bonus for long context models
            else:
                score -= 20  # Penalty for insufficient context

        # Provider health check
        health = await self.check_provider_health(capabilities.provider)
        if not health["available"]:
            score = -1000  # Effectively disable unavailable providers
        else:
            score += health["success_rate"] * 10

        return score

    async def check_provider_health(self, provider_name: str) -> Dict[str, Any]:
        """Check health status of a provider"""
        # Check cache first
        cache_key = f"{provider_name}_health"
        if cache_key in self.health_cache:
            cached = self.health_cache[cache_key]
            if cached["timestamp"] > datetime.now() - timedelta(minutes=1):
                return cached["data"]

        # Simulate health check (in production, actually ping the provider)
        health_data = {
            "available": random.random() > 0.05,  # 95% availability
            "latency_ms": random.uniform(100, 1000),
            "success_rate": random.uniform(0.95, 1.0),
            "status": "healthy" if random.random() > 0.1 else "degraded"
        }

        # Cache the result
        self.health_cache[cache_key] = {
            "timestamp": datetime.now(),
            "data": health_data
        }

        return health_data

    def _create_provider_config(self, capabilities: ModelCapabilities) -> Dict[str, Any]:
        """Create provider configuration for API call"""
        return {
            "name": capabilities.provider,
            "model": capabilities.name,
            "capabilities": capabilities,
            "client": self._get_client(capabilities.provider)  # Would return actual client
        }

    def _get_client(self, provider: str):
        """Get API client for provider"""
        # Create mock client objects for development
        class MockClient:
            async def complete(self, **kwargs):
                return {
                    "text": f"Mock response from {provider} model",
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }

        return MockClient()

    def get_providers(self) -> List[str]:
        """Get list of all provider names"""
        return list(set(cap.provider for cap in self.providers.values()))

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names"""
        available = []
        for model_name, cap in self.providers.items():
            health = asyncio.run(self.check_provider_health(cap.provider))
            if health["available"]:
                available.append(model_name)
        return available
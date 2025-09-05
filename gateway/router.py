"""
Intelligent routing logic for selecting optimal AI provider
Based on requirements, cost, latency, and capabilities
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
    cost_per_1k_tokens: float
    quality_score: float  # 0-1 score
    specialties: List[str]  # e.g., ["code", "reasoning", "creative"]

class IntelligentRouter:
    """Routes requests to optimal AI provider based on multiple factors"""
    
    def __init__(self):
        self.providers = self._initialize_providers()
        self.health_cache = {}
        self.performance_history = []
        
    def _initialize_providers(self) -> Dict[str, ModelCapabilities]:
        """Initialize provider configurations"""
        return {
            "gpt-4-turbo": ModelCapabilities(
                name="gpt-4-turbo",
                provider="openai",
                context_length=128000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=800,
                cost_per_1k_tokens=0.03,
                quality_score=0.95,
                specialties=["reasoning", "creative", "analysis"]
            ),
            "claude-3-opus": ModelCapabilities(
                name="claude-3-opus",
                provider="anthropic",
                context_length=200000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=900,
                cost_per_1k_tokens=0.03,
                quality_score=0.96,
                specialties=["code", "reasoning", "long-form"]
            ),
            "gemini-pro": ModelCapabilities(
                name="gemini-pro",
                provider="google",
                context_length=32000,
                supports_functions=True,
                supports_vision=True,
                supports_streaming=True,
                avg_latency_ms=600,
                cost_per_1k_tokens=0.001,
                quality_score=0.88,
                specialties=["multimodal", "reasoning"]
            ),
            "mistral-medium": ModelCapabilities(
                name="mistral-medium",
                provider="mistral",
                context_length=32000,
                supports_functions=True,
                supports_vision=False,
                supports_streaming=True,
                avg_latency_ms=400,
                cost_per_1k_tokens=0.0027,
                quality_score=0.85,
                specialties=["code", "multilingual"]
            ),
            "mixtral-8x7b": ModelCapabilities(
                name="mixtral-8x7b",
                provider="groq",
                context_length=32000,
                supports_functions=False,
                supports_vision=False,
                supports_streaming=True,
                avg_latency_ms=200,
                cost_per_1k_tokens=0.0005,
                quality_score=0.82,
                specialties=["fast-inference", "code"]
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
        best_model = max(scores, key=scores.get)
        logger.info(f"Selected {best_model} with score {scores[best_model]:.2f}")
        
        return self._create_provider_config(self.providers[best_model])
    
    def _classify_task(self, prompt: str) -> str:
        """Classify the type of task based on prompt content"""
        prompt_lower = prompt.lower()
        
        # Simple keyword-based classification (can be enhanced with ML)
        if any(keyword in prompt_lower for keyword in ["code", "function", "debug", "program"]):
            return "code"
        elif any(keyword in prompt_lower for keyword in ["story", "poem", "creative", "imagine"]):
            return "creative"
        elif any(keyword in prompt_lower for keyword in ["analyze", "explain", "summarize", "reasoning"]):
            return "reasoning"
        elif any(keyword in prompt_lower for keyword in ["translate", "language", "french", "spanish"]):
            return "multilingual"
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
            cost_score = max(0, 100 - (capabilities.cost_per_1k_tokens * 1000))
            score += cost_score * 0.3
        
        # Context length check
        if prompt_length > capabilities.context_length * 0.5:  # Using 50% as threshold
            score -= 20
        
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
        """Get API client for provider (placeholder)"""
        # In production, return actual initialized client
        return f"{provider}_client"
    
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

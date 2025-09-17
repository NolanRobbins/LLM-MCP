"""
Unit tests for AI Gateway components
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.llm_mcp.gateway.router import IntelligentRouter, ModelCapabilities
from src.llm_mcp.gateway.cost_tracker import CostOptimizer
from src.llm_mcp.gateway.metrics import MetricsCollector
from src.llm_mcp.gateway.cache import SemanticCache
from src.llm_mcp.gateway.rate_limiter import AdaptiveRateLimiter

class TestIntelligentRouter:
    """Test cases for IntelligentRouter"""
    
    def setup_method(self):
        self.router = IntelligentRouter()
    
    def test_initialize_providers(self):
        """Test provider initialization"""
        assert len(self.router.providers) > 0
        assert "gpt-4-turbo" in self.router.providers
        assert "claude-3-opus" in self.router.providers
    
    def test_classify_task(self):
        """Test task classification"""
        assert self.router._classify_task("Write a Python function") == "code"
        assert self.router._classify_task("Tell me a story") == "creative"
        assert self.router._classify_task("Explain quantum physics") == "reasoning"
        assert self.router._classify_task("Translate to French") == "multilingual"
        assert self.router._classify_task("Hello world") == "general"
    
    @pytest.mark.asyncio
    async def test_route_request_auto(self):
        """Test automatic routing"""
        result = await self.router.route_request(
            prompt="Write a Python function",
            preferred_model="auto",
            requirements={"low_latency": True}
        )
        
        assert "name" in result
        assert "model" in result
        assert "client" in result
    
    @pytest.mark.asyncio
    async def test_route_request_specific_model(self):
        """Test routing to specific model"""
        result = await self.router.route_request(
            prompt="Test prompt",
            preferred_model="gpt-4-turbo",
            requirements={}
        )
        
        assert result["model"] == "gpt-4-turbo"
        assert result["name"] == "openai"

class TestCostOptimizer:
    """Test cases for CostOptimizer"""
    
    def setup_method(self):
        self.optimizer = CostOptimizer()
    
    def test_calculate_cost(self):
        """Test cost calculation"""
        cost = self.optimizer.calculate_cost(
            provider="openai",
            model="gpt-4-turbo",
            input_tokens=1000,
            output_tokens=500
        )
        
        assert cost > 0
        assert isinstance(cost, float)
    
    def test_cost_report(self):
        """Test cost report generation"""
        # Add some test usage
        self.optimizer._track_usage("openai", "gpt-4-turbo", 0.05)
        self.optimizer._track_usage("anthropic", "claude-3-opus", 0.08)
        
        report = self.optimizer.get_cost_report("1h")
        
        assert "total_cost" in report
        assert "by_provider" in report
        assert "by_model" in report
        assert report["total_cost"] > 0
    
    def test_predict_cost(self):
        """Test cost prediction"""
        predictions = self.optimizer.predict_cost(
            prompt_length=1000,
            expected_output=500,
            model="auto"
        )
        
        assert len(predictions) > 0
        for model, data in predictions.items():
            assert "total_cost" in data
            assert "provider" in data

class TestMetricsCollector:
    """Test cases for MetricsCollector"""
    
    def setup_method(self):
        self.metrics = MetricsCollector()
    
    def test_record_request(self):
        """Test request recording"""
        self.metrics.record_request(
            provider="openai",
            model="gpt-4-turbo",
            latency_ms=500.0,
            cost=0.05,
            success=True
        )
        
        assert len(self.metrics.request_metrics) == 1
        assert self.metrics.provider_metrics["openai"]["requests"] == 1
        assert self.metrics.provider_metrics["openai"]["successes"] == 1
    
    def test_record_cache_hit(self):
        """Test cache hit recording"""
        self.metrics.record_cache_hit()
        self.metrics.record_cache_miss()
        
        assert self.metrics.cache_hits == 1
        assert self.metrics.cache_misses == 1
    
    @pytest.mark.asyncio
    async def test_get_metrics(self):
        """Test metrics retrieval"""
        # Add some test data
        self.metrics.record_request("openai", "gpt-4-turbo", 500.0, 0.05, True)
        self.metrics.record_request("anthropic", "claude-3-opus", 600.0, 0.08, True)
        
        metrics = await self.metrics.get_metrics("1h")
        
        assert "total_requests" in metrics
        assert "success_rate" in metrics
        assert "latency" in metrics
        assert "cost" in metrics
        assert metrics["total_requests"] == 2

class TestSemanticCache:
    """Test cases for SemanticCache"""
    
    def setup_method(self):
        self.cache = SemanticCache(similarity_threshold=0.9, ttl_hours=1)
    
    @pytest.mark.asyncio
    async def test_store_and_find(self):
        """Test storing and finding cached responses"""
        await self.cache.store(
            prompt="What is AI?",
            response="AI is artificial intelligence",
            model="gpt-4-turbo",
            latency_ms=500.0
        )
        
        result = await self.cache.find_similar("What is artificial intelligence?")
        
        assert result is not None
        assert "text" in result
        assert result["text"] == "AI is artificial intelligence"
        assert result["model"] == "gpt-4-turbo"
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics"""
        await self.cache.store(
            prompt="Test prompt",
            response="Test response",
            model="gpt-4-turbo",
            latency_ms=500.0
        )
        
        stats = await self.cache.get_stats()
        
        assert stats["total_entries"] == 1
        assert "gpt-4-turbo" in stats["model_distribution"]

class TestAdaptiveRateLimiter:
    """Test cases for AdaptiveRateLimiter"""
    
    def setup_method(self):
        self.limiter = AdaptiveRateLimiter(
            default_requests_per_minute=10,
            default_requests_per_hour=100,
            burst_limit=5
        )
    
    def test_should_throttle(self):
        """Test rate limiting logic"""
        user_id = "test_user"
        
        # Should not throttle initially
        assert not self.limiter.should_throttle(user_id)
        
        # Record requests up to burst limit
        for _ in range(5):
            self.limiter.record_request(user_id)
        
        # Should throttle after burst limit
        assert self.limiter.should_throttle(user_id)
    
    def test_user_stats(self):
        """Test user statistics"""
        user_id = "test_user"
        
        self.limiter.record_request(user_id)
        stats = self.limiter.get_user_stats(user_id)
        
        assert stats["user_id"] == user_id
        assert stats["requests_last_minute"] == 1
        assert "rpm_limit" in stats
        assert "rph_limit" in stats
    
    def test_adaptive_limits(self):
        """Test adaptive rate limiting"""
        # Normal load
        self.limiter.update_load(0.5)
        assert self.limiter.adaptive_multiplier == 1.0
        
        # High load
        self.limiter.update_load(0.9)
        assert self.limiter.adaptive_multiplier < 1.0
        
        # Low load
        self.limiter.update_load(0.2)
        assert self.limiter.adaptive_multiplier > 1.0

if __name__ == "__main__":
    pytest.main([__file__])

"""
Cost tracking and optimization for multi-provider AI gateway
Tracks usage, predicts costs, and provides optimization recommendations
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class CostModel:
    """Cost model for a provider/model combination"""
    provider: str
    model: str
    input_cost_per_1k: float  # Cost per 1000 input tokens
    output_cost_per_1k: float  # Cost per 1000 output tokens
    request_cost: float  # Fixed cost per request (if any)

class CostOptimizer:
    """Tracks costs and provides optimization recommendations"""
    
    def __init__(self):
        self.cost_models = self._initialize_cost_models()
        self.usage_history = []
        self.cost_by_user = {}
        self.cost_by_provider = {}
        
    def _initialize_cost_models(self) -> Dict[str, CostModel]:
        """Initialize cost models for 2025 providers"""
        return {
            # OpenAI 2025 Models (per 1M tokens)
            "gpt-5": CostModel(
                provider="openai",
                model="gpt-5",
                input_cost_per_1k=3.0,  # $3 per 1M = $0.003 per 1K
                output_cost_per_1k=15.0,  # $15 per 1M = $0.015 per 1K
                request_cost=0
            ),
            "o3": CostModel(
                provider="openai",
                model="o3",
                input_cost_per_1k=15.0,  # $15 per 1M = $0.015 per 1K
                output_cost_per_1k=60.0,  # $60 per 1M = $0.060 per 1K
                request_cost=0
            ),
            "o4-mini": CostModel(
                provider="openai",
                model="o4-mini",
                input_cost_per_1k=0.15,  # $0.15 per 1M = $0.00015 per 1K
                output_cost_per_1k=0.60,  # $0.60 per 1M = $0.0006 per 1K
                request_cost=0
            ),
            # Anthropic 2025 Models
            "claude-opus-4.1": CostModel(
                provider="anthropic",
                model="claude-opus-4.1",
                input_cost_per_1k=15.0,  # $15 per 1M
                output_cost_per_1k=75.0,  # $75 per 1M
                request_cost=0
            ),
            "claude-sonnet-4": CostModel(
                provider="anthropic",
                model="claude-sonnet-4",
                input_cost_per_1k=3.0,  # $3 per 1M
                output_cost_per_1k=15.0,  # $15 per 1M
                request_cost=0
            ),
            # Google 2025 Models
            "gemini-2.5-pro": CostModel(
                provider="google",
                model="gemini-2.5-pro",
                input_cost_per_1k=1.25,  # $1.25 per 1M
                output_cost_per_1k=5.0,  # $5 per 1M
                request_cost=0
            ),
            "gemini-2.5-flash": CostModel(
                provider="google",
                model="gemini-2.5-flash",
                input_cost_per_1k=0.075,  # $0.075 per 1M
                output_cost_per_1k=0.30,  # $0.30 per 1M
                request_cost=0
            ),
            # xAI 2025 Models
            "grok-4": CostModel(
                provider="xai",
                model="grok-4",
                input_cost_per_1k=5.0,  # $5 per 1M
                output_cost_per_1k=15.0,  # $15 per 1M
                request_cost=0
            ),
            "grok-4-heavy": CostModel(
                provider="xai",
                model="grok-4-heavy",
                input_cost_per_1k=10.0,  # $10 per 1M
                output_cost_per_1k=30.0,  # $30 per 1M
                request_cost=0
            )
        }
    
    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate cost for a request
        
        Args:
            provider: Provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Total cost in USD
        """
        if model not in self.cost_models:
            logger.warning(f"Unknown model {model}, using default cost")
            return 0.001  # Default cost
        
        cost_model = self.cost_models[model]
        
        input_cost = (input_tokens / 1000) * cost_model.input_cost_per_1k
        output_cost = (output_tokens / 1000) * cost_model.output_cost_per_1k
        total_cost = input_cost + output_cost + cost_model.request_cost
        
        # Track usage
        self._track_usage(provider, model, total_cost)
        
        return total_cost
    
    def _track_usage(self, provider: str, model: str, cost: float) -> None:
        """Track usage for analytics"""
        usage = {
            "timestamp": datetime.now(),
            "provider": provider,
            "model": model,
            "cost": cost
        }
        
        self.usage_history.append(usage)
        
        # Update aggregates
        if provider not in self.cost_by_provider:
            self.cost_by_provider[provider] = 0
        self.cost_by_provider[provider] += cost
        
        # Keep only last 24 hours of history
        cutoff = datetime.now() - timedelta(hours=24)
        self.usage_history = [
            u for u in self.usage_history 
            if u["timestamp"] > cutoff
        ]
    
    def get_cost_report(
        self,
        time_range: str = "24h"
    ) -> Dict[str, any]:
        """
        Generate cost report for specified time range
        
        Args:
            time_range: Time range (1h, 24h, 7d, 30d)
            
        Returns:
            Cost breakdown and statistics
        """
        # Parse time range
        hours = {
            "1h": 1,
            "24h": 24,
            "7d": 168,
            "30d": 720
        }.get(time_range, 24)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filter usage by time range
        filtered = [
            u for u in self.usage_history 
            if u["timestamp"] > cutoff
        ]
        
        # Calculate statistics
        total_cost = sum(u["cost"] for u in filtered)
        
        # Group by provider
        by_provider = {}
        for usage in filtered:
            provider = usage["provider"]
            if provider not in by_provider:
                by_provider[provider] = {"cost": 0, "count": 0}
            by_provider[provider]["cost"] += usage["cost"]
            by_provider[provider]["count"] += 1
        
        # Group by model
        by_model = {}
        for usage in filtered:
            model = usage["model"]
            if model not in by_model:
                by_model[model] = {"cost": 0, "count": 0}
            by_model[model]["cost"] += usage["cost"]
            by_model[model]["count"] += 1
        
        return {
            "time_range": time_range,
            "total_cost": total_cost,
            "total_requests": len(filtered),
            "avg_cost_per_request": total_cost / len(filtered) if filtered else 0,
            "by_provider": by_provider,
            "by_model": by_model,
            "hourly_rate": total_cost / hours if hours > 0 else 0,
            "projected_monthly": (total_cost / hours * 720) if hours > 0 else 0
        }
    
    def recommend_optimization(
        self,
        current_usage: Dict[str, int]
    ) -> List[Dict[str, any]]:
        """
        Provide optimization recommendations based on usage patterns
        
        Args:
            current_usage: Current usage patterns by model
            
        Returns:
            List of recommendations with potential savings
        """
        recommendations = []
        
        # Analyze each model's usage
        for model, count in current_usage.items():
            if model not in self.cost_models:
                continue
            
            current_model = self.cost_models[model]
            
            # Find cheaper alternatives
            for alt_model, alt_cost in self.cost_models.items():
                if alt_model == model:
                    continue
                
                # Calculate potential savings
                current_cost = current_model.output_cost_per_1k
                alt_cost_val = alt_cost.output_cost_per_1k
                
                if alt_cost_val < current_cost * 0.5:  # 50% cheaper
                    savings_pct = (1 - alt_cost_val / current_cost) * 100
                    
                    recommendations.append({
                        "current_model": model,
                        "recommended_model": alt_model,
                        "reason": "significant_cost_reduction",
                        "potential_savings_pct": savings_pct,
                        "trade_off": self._get_tradeoff(model, alt_model)
                    })
        
        # Add caching recommendation if not using it
        if len(self.usage_history) > 100:
            duplicate_rate = self._calculate_duplicate_rate()
            if duplicate_rate > 0.1:  # More than 10% duplicates
                recommendations.append({
                    "type": "enable_caching",
                    "reason": "high_duplicate_rate",
                    "duplicate_rate": duplicate_rate,
                    "potential_savings_pct": duplicate_rate * 100
                })
        
        return recommendations
    
    def _get_tradeoff(self, current: str, alternative: str) -> str:
        """Get trade-off description when switching models"""
        tradeoffs = {
            ("gpt-4-turbo", "gpt-3.5-turbo"): "Lower quality but 20x cheaper",
            ("claude-3-opus", "claude-3-sonnet"): "Slightly lower quality but 5x cheaper",
            ("gpt-4-turbo", "mixtral-8x7b"): "Lower quality but 100x cheaper and faster",
            ("claude-3-opus", "gemini-pro"): "Different strengths but 30x cheaper"
        }
        
        return tradeoffs.get(
            (current, alternative),
            "Different capabilities and cost profile"
        )
    
    def _calculate_duplicate_rate(self) -> float:
        """Calculate rate of duplicate requests (simplified)"""
        # In production, would use actual prompt comparison
        # This is a simplified estimation
        if len(self.usage_history) < 10:
            return 0.0
        
        # Estimate based on time clustering
        timestamps = [u["timestamp"] for u in self.usage_history[-100:]]
        clusters = 0
        
        for i in range(1, len(timestamps)):
            if (timestamps[i] - timestamps[i-1]).seconds < 60:
                clusters += 1
        
        return clusters / len(timestamps) if timestamps else 0.0
    
    def predict_cost(
        self,
        prompt_length: int,
        expected_output: int,
        model: str = "auto"
    ) -> Dict[str, float]:
        """
        Predict cost before making request
        
        Args:
            prompt_length: Estimated prompt length in tokens
            expected_output: Expected output length in tokens
            model: Model to use or "auto"
            
        Returns:
            Predicted costs for different models
        """
        predictions = {}
        
        for model_name, cost_model in self.cost_models.items():
            if model != "auto" and model != model_name:
                continue
            
            input_cost = (prompt_length / 1000) * cost_model.input_cost_per_1k
            output_cost = (expected_output / 1000) * cost_model.output_cost_per_1k
            total = input_cost + output_cost + cost_model.request_cost
            
            predictions[model_name] = {
                "total_cost": total,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "provider": cost_model.provider
            }
        
        return predictions

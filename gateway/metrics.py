"""
Metrics collection and monitoring for AI Gateway
Integrates with Cloud Monitoring and provides real-time analytics
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import statistics
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and aggregates metrics for monitoring"""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        
        # Metrics storage
        self.request_metrics = deque(maxlen=window_size)
        self.provider_metrics = defaultdict(lambda: {
            "requests": 0,
            "successes": 0,
            "failures": 0,
            "total_latency": 0,
            "total_cost": 0
        })
        
        # Cache metrics
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Rate limiting metrics
        self.rate_limit_hits = 0
        
        # Time series data for graphs
        self.time_series = defaultdict(list)
        
    def record_request(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        cost: float,
        success: bool,
        cached: bool = False
    ) -> None:
        """
        Record metrics for a request
        
        Args:
            provider: Provider name
            model: Model name
            latency_ms: Request latency in milliseconds
            cost: Request cost in USD
            success: Whether request succeeded
            cached: Whether response was from cache
        """
        metric = {
            "timestamp": datetime.now(),
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "cost": cost,
            "success": success,
            "cached": cached
        }
        
        self.request_metrics.append(metric)
        
        # Update provider aggregates
        pm = self.provider_metrics[provider]
        pm["requests"] += 1
        if success:
            pm["successes"] += 1
            pm["total_latency"] += latency_ms
            pm["total_cost"] += cost
        else:
            pm["failures"] += 1
        
        # Update time series (keep last 24 hours)
        self._update_time_series(provider, latency_ms, cost, success)
        
        logger.debug(f"Recorded metric: {provider}/{model} - {latency_ms}ms - ${cost:.4f}")
    
    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_rate_limit(self) -> None:
        """Record a rate limit hit"""
        self.rate_limit_hits += 1
    
    def _update_time_series(
        self,
        provider: str,
        latency: float,
        cost: float,
        success: bool
    ) -> None:
        """Update time series data for graphs"""
        now = datetime.now()
        bucket = now.replace(second=0, microsecond=0)  # Round to minute
        
        key = f"{provider}_{bucket}"
        
        if key not in self.time_series:
            self.time_series[key] = {
                "timestamp": bucket,
                "provider": provider,
                "requests": 0,
                "successes": 0,
                "total_latency": 0,
                "total_cost": 0
            }
        
        ts = self.time_series[key]
        ts["requests"] += 1
        if success:
            ts["successes"] += 1
            ts["total_latency"] += latency
            ts["total_cost"] += cost
        
        # Clean old data (keep 24 hours)
        cutoff = now - timedelta(hours=24)
        self.time_series = {
            k: v for k, v in self.time_series.items()
            if v["timestamp"] > cutoff
        }
    
    async def get_metrics(
        self,
        time_range: str = "1h",
        provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for time range
        
        Args:
            time_range: Time range (1h, 24h, 7d, 30d)
            provider: Optional filter by provider
            
        Returns:
            Comprehensive metrics dictionary
        """
        # Parse time range
        hours = {
            "1h": 1,
            "24h": 24,
            "7d": 168,
            "30d": 720
        }.get(time_range, 1)
        
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Filter metrics by time and provider
        filtered = [
            m for m in self.request_metrics
            if m["timestamp"] > cutoff and
            (provider is None or m["provider"] == provider)
        ]
        
        if not filtered:
            return self._empty_metrics(time_range)
        
        # Calculate statistics
        latencies = [m["latency_ms"] for m in filtered if m["success"]]
        costs = [m["cost"] for m in filtered]
        success_count = sum(1 for m in filtered if m["success"])
        failure_count = sum(1 for m in filtered if not m["success"])
        cached_count = sum(1 for m in filtered if m.get("cached", False))
        
        # Provider breakdown
        provider_breakdown = defaultdict(lambda: {
            "requests": 0,
            "successes": 0,
            "avg_latency": 0,
            "total_cost": 0
        })
        
        for metric in filtered:
            pb = provider_breakdown[metric["provider"]]
            pb["requests"] += 1
            if metric["success"]:
                pb["successes"] += 1
                pb["total_cost"] += metric["cost"]
        
        # Calculate averages
        for provider_data in provider_breakdown.values():
            if provider_data["successes"] > 0:
                provider_latencies = [
                    m["latency_ms"] for m in filtered
                    if m["provider"] == provider and m["success"]
                ]
                provider_data["avg_latency"] = statistics.mean(provider_latencies)
        
        # Cache statistics
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = self.cache_hits / cache_total if cache_total > 0 else 0
        
        return {
            "time_range": time_range,
            "total_requests": len(filtered),
            "successful_requests": success_count,
            "failed_requests": failure_count,
            "success_rate": success_count / len(filtered) if filtered else 0,
            "cached_responses": cached_count,
            "cache_hit_rate": cache_hit_rate,
            "latency": {
                "min": min(latencies) if latencies else 0,
                "max": max(latencies) if latencies else 0,
                "mean": statistics.mean(latencies) if latencies else 0,
                "median": statistics.median(latencies) if latencies else 0,
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else 0,
                "p99": statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else 0
            },
            "cost": {
                "total": sum(costs),
                "average": statistics.mean(costs) if costs else 0,
                "min": min(costs) if costs else 0,
                "max": max(costs) if costs else 0
            },
            "provider_breakdown": dict(provider_breakdown),
            "rate_limit_hits": self.rate_limit_hits,
            "requests_per_minute": len(filtered) / (hours * 60) if hours > 0 else 0
        }
    
    def _empty_metrics(self, time_range: str) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            "time_range": time_range,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "success_rate": 0,
            "cached_responses": 0,
            "cache_hit_rate": 0,
            "latency": {
                "min": 0,
                "max": 0,
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0
            },
            "cost": {
                "total": 0,
                "average": 0,
                "min": 0,
                "max": 0
            },
            "provider_breakdown": {},
            "rate_limit_hits": 0,
            "requests_per_minute": 0
        }
    
    def get_health_score(self) -> float:
        """
        Calculate overall health score (0-100)
        
        Returns:
            Health score based on recent metrics
        """
        if not self.request_metrics:
            return 100.0
        
        recent = list(self.request_metrics)[-100:]  # Last 100 requests
        
        if not recent:
            return 100.0
        
        # Calculate factors
        success_rate = sum(1 for m in recent if m["success"]) / len(recent)
        avg_latency = statistics.mean([m["latency_ms"] for m in recent if m["success"]])
        
        # Score calculation
        success_score = success_rate * 50  # 50 points for success rate
        latency_score = max(0, 50 - (avg_latency / 20))  # 50 points for low latency
        
        return min(100, success_score + latency_score)

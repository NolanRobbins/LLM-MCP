"""
Adaptive rate limiting for AI Gateway
Implements sliding window rate limiting with user-based quotas
"""
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import logging

logger = logging.getLogger(__name__)

class AdaptiveRateLimiter:
    """Adaptive rate limiter with sliding window and user quotas"""
    
    def __init__(
        self,
        default_requests_per_minute: int = 60,
        default_requests_per_hour: int = 1000,
        burst_limit: int = 10
    ):
        self.default_rpm = default_requests_per_minute
        self.default_rph = default_requests_per_hour
        self.burst_limit = burst_limit
        
        # Per-user rate limiting
        self.user_requests = defaultdict(lambda: {
            "minute_window": deque(),
            "hour_window": deque(),
            "last_request": 0
        })
        
        # Adaptive limits based on system load
        self.current_load = 0.0
        self.adaptive_multiplier = 1.0
        
    def should_throttle(self, user_id: str) -> bool:
        """
        Check if a user should be throttled
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user should be throttled
        """
        now = time.time()
        user_data = self.user_requests[user_id]
        
        # Clean old requests from windows
        self._clean_windows(user_data, now)
        
        # Check burst limit
        if len(user_data["minute_window"]) >= self.burst_limit:
            logger.warning(f"User {user_id} hit burst limit")
            return True
        
        # Check per-minute limit
        rpm_limit = int(self.default_rpm * self.adaptive_multiplier)
        if len(user_data["minute_window"]) >= rpm_limit:
            logger.warning(f"User {user_id} exceeded RPM limit: {rpm_limit}")
            return True
        
        # Check per-hour limit
        rph_limit = int(self.default_rph * self.adaptive_multiplier)
        if len(user_data["hour_window"]) >= rph_limit:
            logger.warning(f"User {user_id} exceeded RPH limit: {rph_limit}")
            return True
        
        return False
    
    def record_request(self, user_id: str) -> None:
        """
        Record a request for a user
        
        Args:
            user_id: User identifier
        """
        now = time.time()
        user_data = self.user_requests[user_id]
        
        # Add request to windows
        user_data["minute_window"].append(now)
        user_data["hour_window"].append(now)
        user_data["last_request"] = now
        
        logger.debug(f"Recorded request for user {user_id}")
    
    def get_retry_after(self, user_id: str) -> int:
        """
        Get retry-after time in seconds for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            Seconds to wait before retrying
        """
        user_data = self.user_requests[user_id]
        
        if not user_data["minute_window"]:
            return 0
        
        # Calculate time until oldest request in minute window expires
        oldest_request = user_data["minute_window"][0]
        retry_after = int(60 - (time.time() - oldest_request))
        
        return max(0, retry_after)
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get rate limiting stats for a user
        
        Args:
            user_id: User identifier
            
        Returns:
            User statistics
        """
        now = time.time()
        user_data = self.user_requests[user_id]
        
        # Clean windows
        self._clean_windows(user_data, now)
        
        return {
            "user_id": user_id,
            "requests_last_minute": len(user_data["minute_window"]),
            "requests_last_hour": len(user_data["hour_window"]),
            "last_request": user_data["last_request"],
            "rpm_limit": int(self.default_rpm * self.adaptive_multiplier),
            "rph_limit": int(self.default_rph * self.adaptive_multiplier),
            "burst_limit": self.burst_limit
        }
    
    def update_load(self, current_load: float) -> None:
        """
        Update system load for adaptive rate limiting
        
        Args:
            current_load: Current system load (0.0 to 1.0)
        """
        self.current_load = current_load
        
        # Adjust multiplier based on load
        if current_load > 0.8:
            self.adaptive_multiplier = 0.5  # Reduce limits by 50%
        elif current_load > 0.6:
            self.adaptive_multiplier = 0.7  # Reduce limits by 30%
        elif current_load < 0.3:
            self.adaptive_multiplier = 1.2  # Increase limits by 20%
        else:
            self.adaptive_multiplier = 1.0  # Normal limits
        
        logger.info(f"Updated adaptive multiplier to {self.adaptive_multiplier} (load: {current_load})")
    
    def _clean_windows(self, user_data: Dict[str, Any], now: float) -> None:
        """Clean old requests from time windows"""
        # Clean minute window (keep last 60 seconds)
        minute_cutoff = now - 60
        while user_data["minute_window"] and user_data["minute_window"][0] < minute_cutoff:
            user_data["minute_window"].popleft()
        
        # Clean hour window (keep last 3600 seconds)
        hour_cutoff = now - 3600
        while user_data["hour_window"] and user_data["hour_window"][0] < hour_cutoff:
            user_data["hour_window"].popleft()
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global rate limiting statistics"""
        now = time.time()
        active_users = 0
        total_requests_minute = 0
        total_requests_hour = 0
        
        for user_data in self.user_requests.values():
            self._clean_windows(user_data, now)
            
            if user_data["minute_window"] or user_data["hour_window"]:
                active_users += 1
                total_requests_minute += len(user_data["minute_window"])
                total_requests_hour += len(user_data["hour_window"])
        
        return {
            "active_users": active_users,
            "total_requests_last_minute": total_requests_minute,
            "total_requests_last_hour": total_requests_hour,
            "current_load": self.current_load,
            "adaptive_multiplier": self.adaptive_multiplier,
            "default_rpm": self.default_rpm,
            "default_rph": self.default_rph,
            "burst_limit": self.burst_limit
        }
    
    def reset_user_limits(self, user_id: str) -> None:
        """Reset rate limits for a specific user"""
        if user_id in self.user_requests:
            self.user_requests[user_id] = {
                "minute_window": deque(),
                "hour_window": deque(),
                "last_request": 0
            }
            logger.info(f"Reset rate limits for user {user_id}")
    
    def set_user_limits(
        self,
        user_id: str,
        rpm: Optional[int] = None,
        rph: Optional[int] = None,
        burst: Optional[int] = None
    ) -> None:
        """
        Set custom rate limits for a user
        
        Args:
            user_id: User identifier
            rpm: Requests per minute
            rph: Requests per hour
            burst: Burst limit
        """
        # This would be implemented with a user limits configuration
        # For now, just log the request
        logger.info(f"Setting custom limits for user {user_id}: RPM={rpm}, RPH={rph}, Burst={burst}")

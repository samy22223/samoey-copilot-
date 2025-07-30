from datetime import datetime, timedelta
from typing import Dict, Optional
import time

class RateLimitException(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

class RateLimitManager:
    """Rate limit manager using sliding window algorithm"""
    
    def __init__(self, rate_limit: int, time_window: int):
        """Initialize rate limiter
        
        Args:
            rate_limit (int): Maximum number of requests allowed
            time_window (int): Time window in seconds
        """
        self.rate_limit = rate_limit
        self.time_window = time_window
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for given key
        
        Args:
            key (str): Identifier for the client (e.g. IP address)
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        # Initialize if key not found
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove expired timestamps
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > current_time - self.time_window
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= self.rate_limit:
            return False
        
        # Add current request timestamp
        self.requests[key].append(current_time)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for given key
        
        Args:
            key (str): Identifier for the client
            
        Returns:
            int: Number of remaining requests allowed
        """
        if key not in self.requests:
            return self.rate_limit
        
        current_time = time.time()
        valid_requests = [
            ts for ts in self.requests[key]
            if ts > current_time - self.time_window
        ]
        
        return max(0, self.rate_limit - len(valid_requests))
    
    def reset(self, key: str) -> None:
        """Reset rate limit for given key
        
        Args:
            key (str): Identifier for the client
        """
        if key in self.requests:
            del self.requests[key]

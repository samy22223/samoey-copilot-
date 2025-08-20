"""
Security Middleware for FastAPI Applications

This module provides a comprehensive security middleware implementation for FastAPI
applications, including:
- IP-based access control and rate limiting
- Security threat detection and prevention
- Request validation and sanitization
- Comprehensive logging and monitoring
- Cache-based performance optimization
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR
)
from typing import Dict, List, Optional, Tuple, Any, Union, Set
import re
import time
import json
import uuid
import ipaddress

from datetime import datetime, timedelta
import hashlib
from ratelimit import RateLimitException, RateLimitManager
from prometheus_client import Counter, Histogram, Gauge

from config.settings import settings
from ..core.logging import get_logger
from ..core.redis import get_redis, RedisError
from ..core.errors import (
    RateLimitError,
    SecurityError,
    ConfigurationError,
    ValidationError,
    ErrorCode
)
from ..core.security_context import SecurityContext
from ..core.metrics import get_metrics
from ..core.utils.validation import validate_ip, validate_cidr
from ..core.cache import Cache, CacheError

# Configure logging
logger = get_logger(__name__)

# Initialize metrics
SECURITY_VIOLATIONS = Counter(
    'security_violations_total',
    'Total number of security violations',
    ['type', 'severity']
)
REQUEST_PROCESSING_TIME = Histogram(
    'security_request_processing_seconds',
    'Time spent processing requests through security middleware'
)
ACTIVE_BLOCKS = Gauge(
    'security_active_blocks',
    'Number of currently blocked IPs'
)

class SecurityConfigError(ConfigurationError):
    """Raised when there's an error in security configuration"""
    pass

class SecurityValidationError(ValidationError):
    """Raised when security validation fails"""
    pass

class SecurityBlockError(SecurityError):
    """Raised when an IP or request is blocked"""
    pass

class SecurityThrottleError(RateLimitError):
    """Raised when request rate limits are exceeded"""
    pass

# --- SecurityCache ---
class SecurityCache(Cache):
    """Specialized cache for security-related data"""
    
    def __init__(self, redis_prefix: str = "security"):
        super().__init__(redis_prefix)
        self.default_ttl = 300  # 5 minutes
        
    async def get_block_status(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get block status for an IP"""
        try:
            data = await self.get(f"block:{ip}")
            return json.loads(data) if data else None
        except (json.JSONDecodeError, CacheError) as e:
            logger.error(f"Error getting block status for {ip}: {e}")
            return None
            
    async def set_block_status(
        self,
        ip: str,
        reason: str,
        duration: int,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Set block status for an IP"""
        try:
            data = {
                "ip": ip,
                "reason": reason,
                "blocked_at": datetime.now().isoformat(),
                "duration": duration,
                "details": details or {}
            }
            return await self.set(
                f"block:{ip}",
                json.dumps(data),
                ttl=duration
            )
        except CacheError as e:
            logger.error(f"Error setting block status for {ip}: {e}")
            return False

# --- SecurityMetrics ---
class SecurityMetrics:
    """Handle security-related metrics"""
    
    def __init__(self):
        self.violations = SECURITY_VIOLATIONS
        self.processing_time = REQUEST_PROCESSING_TIME
        self.active_blocks = ACTIVE_BLOCKS
        
    def record_violation(self, type_: str, severity: str):
        """Record a security violation"""
        self.violations.labels(type=type_, severity=severity).inc()
        
    def record_processing_time(self, seconds: float):
        """Record request processing time"""
        self.processing_time.observe(seconds)
        
    def update_active_blocks(self, count: int):
        """Update count of active blocks"""
        self.active_blocks.set(count)

# --- RequestValidator ---
class RequestValidator:
    """Validate and sanitize requests"""
    
    def __init__(self):
        self.ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        self.cidr_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
        self.path_traversal_pattern = re.compile(r"\.\.\/|\.\.\\")
        
    def validate_ip(self, ip: str) -> bool:
        """Validate IP address format"""
        if not self.ip_pattern.match(ip):
            return False
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
            
    def validate_cidr(self, cidr: str) -> bool:
        """Validate CIDR notation"""
        if not self.cidr_pattern.match(cidr):
            return False
        try:
            ipaddress.ip_network(cidr)
            return True
        except ValueError:
            return False
            
    def sanitize_path(self, path: str) -> str:
        """Sanitize request path"""
        return re.sub(r'[^a-zA-Z0-9/._-]', '', path)
        
    def validate_request_size(self, size: int, max_size: int) -> bool:
        """Validate request size"""
        return 0 <= size <= max_size

# --- SecurityContext ---
class SecurityContext:
    """Manage security context for requests"""
    
    def __init__(self):
        self.cache = SecurityCache()
        self.metrics = SecurityMetrics()
        self.validator = RequestValidator()
        self._redis = None
        self._initialized = False
        
    async def __aenter__(self):
        """Initialize security context"""
        if not self._initialized:
            await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup security context"""
        if exc_type is not None:
            logger.error(f"Error in security context: {exc_val}")
        await self.cleanup()
        
    async def initialize(self):
        """Initialize security context"""
        try:
            self._redis = await get_redis()
            self._initialized = True
        except RedisError as e:
            logger.error(f"Failed to initialize security context: {e}")
            raise SecurityConfigError("Failed to initialize security context")
            
    async def cleanup(self):
        """Cleanup security context"""
        # Implement cleanup logic here
        pass
        
    async def check_block_status(self, ip: str) -> Optional[Dict[str, Any]]:
        """Check if an IP is blocked"""
        return await self.cache.get_block_status(ip)
        
    async def block_ip(
        self,
        ip: str,
        reason: str,
        duration: int,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Block an IP address"""
        success = await self.cache.set_block_status(ip, reason, duration, details)
        if success:
            self.metrics.update_active_blocks(await self._count_active_blocks())
        return success
        
    async def _count_active_blocks(self) -> int:
        """Count number of currently blocked IPs"""
        try:
            keys = await self._redis.keys("security:block:*")
            return len(keys)
        except RedisError:
            return 0

class ThreatAnalyzer:
    """Analyze requests for security threats"""
    
    def __init__(self):
        # SQL injection patterns
        self.sql_patterns = [
            r"(?i)(select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from)",
            r"(?i)(union\s+select|drop\s+table|alter\s+table|exec\s*\(|\;\s*exec)",
            r"(?i)(xp_cmdshell|sp_executesql|sp_execute|sp_help|sp_who)"
        ]
        
        # XSS patterns
        self.xss_patterns = [
            r"(?i)(<script|javascript:|data:text/html|vbscript:|<img|<svg)",
            r"(?i)(onload=|onerror=|onmouseover=|onclick=|onsubmit=)",
            r"(?i)(alert\(|eval\(|document\.cookie|document\.write)"
        ]
        
        # Command injection patterns
        self.cmd_patterns = [
            r"(?i)([;&|`\$]|bash\s+-i|nc\s+-e|python\s+-c)",
            r"(?i)(wget\s+http|curl\s+http|chmod\s+[0-7]{3,4})",
            r"(?i)(cat\s+/etc/passwd|cat\s+/etc/shadow|/bin/sh)"
        ]
        
        # Suspicious header patterns
        self.header_patterns = {
            "user-agent": r"(?i)(curl|wget|nikto|sqlmap|arachni|nmap|burp|acunetix)",
            "x-forwarded-for": r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            "referer": r"(?i)(localhost|127\.0\.0\.1|0\.0\.0\.0)",
            "cookie": r"(?i)(document\.cookie|<script|alert\()"
        }
        
        # Compile all patterns
        self.compile_patterns()
        
    def compile_patterns(self):
        """Compile regex patterns"""
        self.sql_regex = [re.compile(p) for p in self.sql_patterns]
        self.xss_regex = [re.compile(p) for p in self.xss_patterns]
        self.cmd_regex = [re.compile(p) for p in self.cmd_patterns]
        self.header_regex = {
            k: re.compile(v) for k, v in self.header_patterns.items()
        }
        
    def analyze_request(
        self,
        headers: Dict[str, str],
        path: str,
        query_params: Dict[str, str],
        body: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Analyze request for security threats"""
        threats = []
        
        # Check headers
        threats.extend(self.check_headers(headers))
        
        # Check path
        threats.extend(self.check_path(path))
        
        # Check query parameters
        threats.extend(self.check_params(query_params))
        
        # Check body if present
        if body:
            threats.extend(self.check_body(body))
            
        return threats
        
    def check_headers(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check headers for threats"""
        threats = []
        for header, value in headers.items():
            header_lower = header.lower()
            if header_lower in self.header_regex:
                if self.header_regex[header_lower].search(value):
                    threats.append({
                        "type": "suspicious_header",
                        "severity": "medium",
                        "details": {
                            "header": header,
                            "value": value[:100]
                        }
                    })
        return threats
        
    def check_path(self, path: str) -> List[Dict[str, Any]]:
        """Check path for threats"""
        threats = []
        # Add path checking logic
        return threats
        
    def check_params(self, params: Dict[str, str]) -> List[Dict[str, Any]]:
        """Check query parameters for threats"""
        threats = []
        for param, value in params.items():
            if any(r.search(value) for r in self.sql_regex):
                threats.append({
                    "type": "sql_injection",
                    "severity": "high",
                    "details": {"parameter": param}
                })
            if any(r.search(value) for r in self.xss_regex):
                threats.append({
                    "type": "xss",
                    "severity": "high",
                    "details": {"parameter": param}
                })
            if any(r.search(value) for r in self.cmd_regex):
                threats.append({
                    "type": "command_injection",
                    "severity": "critical",
                    "details": {"parameter": param}
                })
        return threats
        
    def check_body(self, body: str) -> List[Dict[str, Any]]:
        """Check request body for threats"""
        threats = []
        if any(r.search(body) for r in self.sql_regex):
            threats.append({
                "type": "sql_injection",
                "severity": "high",
                "details": {"location": "body"}
            })
        if any(r.search(body) for r in self.xss_regex):
            threats.append({
                "type": "xss",
                "severity": "high",
                "details": {"location": "body"}
            })
        if any(r.search(body) for r in self.cmd_regex):
            threats.append({
                "type": "command_injection",
                "severity": "critical",
                "details": {"location": "body"}
            })
        return threats

class RateLimiter:
    """Advanced rate limiting with exponential backoff"""
    
    def __init__(self, redis_prefix: str = "ratelimit"):
        self.redis_prefix = redis_prefix
        self.cache = SecurityCache(redis_prefix)
        self.metrics = SecurityMetrics()
        
        # Rate limit windows (in seconds)
        self.windows = {
            "per_second": 1,
            "per_minute": 60,
            "per_hour": 3600,
            "per_day": 86400
        }
        
        # Default limits
        self.default_limits = {
            "per_second": 10,
            "per_minute": 300,
            "per_hour": 3600,
            "per_day": 10000
        }
        
        # Backoff settings
        self.min_backoff = 1  # seconds
        self.max_backoff = 3600  # 1 hour
        self.backoff_factor = 2
        
    async def check_rate_limit(
        self,
        key: str,
        limits: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if rate limit is exceeded"""
        try:
            limits = limits or self.default_limits
            current_time = int(time.time())
            
            # Check each window
            for window_name, window_size in self.windows.items():
                if window_name not in limits:
                    continue
                    
                window_key = f"{self.redis_prefix}:{key}:{window_name}"
                count = await self._increment_window(window_key, window_size)
                
                if count > limits[window_name]:
                    backoff = await self._calculate_backoff(key, count - limits[window_name])
                    return False, {
                        "window": window_name,
                        "limit": limits[window_name],
                        "current": count,
                        "backoff": backoff,
                        "reset": current_time + backoff
                    }
            
            return True, None
            
        except Exception as e:
            logger.error(f"Rate limit error for {key}: {e}")
            return True, None  # Fail open if rate limiting fails
            
    async def _increment_window(self, key: str, window_size: int) -> int:
        """Increment and get the current count for a window"""
        try:
            redis = await get_redis()
            pipeline = redis.pipeline()
            current_time = int(time.time())
            
            # Remove old entries
            pipeline.zremrangebyscore(key, 0, current_time - window_size)
            # Add new entry
            pipeline.zadd(key, {str(current_time): current_time})
            # Get current count
            pipeline.zcard(key)
            # Set expiry
            pipeline.expire(key, window_size)
            
            results = await pipeline.execute()
            return results[2]  # Return the count
            
        except RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            return 0
            
    async def _calculate_backoff(self, key: str, excess: int) -> int:
        """Calculate exponential backoff time"""
        try:
            backoff_key = f"{self.redis_prefix}:backoff:{key}"
            redis = await get_redis()
            
            # Get current backoff count
            current_backoff = await redis.incr(backoff_key)
            await redis.expire(backoff_key, self.max_backoff)
            
            # Calculate backoff time
            backoff = min(
                self.max_backoff,
                self.min_backoff * (self.backoff_factor ** (current_backoff - 1))
            )
            
            return int(backoff)
            
        except RedisError as e:
            logger.error(f"Redis error in backoff calculation: {e}")
            return self.min_backoff
            
    async def reset_backoff(self, key: str) -> None:
        """Reset backoff counter for a key"""
        try:
            backoff_key = f"{self.redis_prefix}:backoff:{key}"
            redis = await get_redis()
            await redis.delete(backoff_key)
        except RedisError as e:
            logger.error(f"Redis error in backoff reset: {e}")

class ReputationManager:
    """Manage IP reputation scores and tracking"""
    
    def __init__(self, redis_prefix: str = "reputation"):
        self.redis_prefix = redis_prefix
        self.cache = SecurityCache(redis_prefix)
        self.metrics = SecurityMetrics()
        
        # Reputation score ranges
        self.max_score = 100
        self.min_score = -100
        self.initial_score = 50
        
        # Score adjustments
        self.adjustments = {
            "successful_request": 1,
            "failed_request": -1,
            "security_violation": -10,
            "blocked": -20,
            "suspicious_activity": -5,
            "verified_user": 10
        }
        
        # Thresholds
        self.thresholds = {
            "block": -50,
            "warn": -20,
            "verify": 0,
            "trust": 70
        }
        
    async def get_reputation(self, ip: str) -> Dict[str, Any]:
        """Get reputation data for an IP"""
        try:
            key = f"{self.redis_prefix}:{ip}"
            redis = await get_redis()
            
            data = await redis.hgetall(key)
            if not data:
                # Initialize new reputation
                score = self.initial_score
                data = {
                    "score": str(score),
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "events": "[]"
                }
                await redis.hmset(key, data)
            
            # Parse stored data
            events = json.loads(data.get("events", "[]"))
            return {
                "ip": ip,
                "score": float(data.get("score", self.initial_score)),
                "created_at": data.get("created_at"),
                "last_updated": data.get("last_updated"),
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Error getting reputation for {ip}: {e}")
            return {
                "ip": ip,
                "score": self.initial_score,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "events": []
            }
            
    async def update_reputation(
        self,
        ip: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update reputation score for an IP"""
        try:
            if event_type not in self.adjustments:
                return await self.get_reputation(ip)
                
            key = f"{self.redis_prefix}:{ip}"
            redis = await get_redis()
            
            # Get current reputation
            rep = await self.get_reputation(ip)
            current_score = rep["score"]
            events = rep["events"]
            
            # Calculate new score
            adjustment = self.adjustments[event_type]
            new_score = max(
                self.min_score,
                min(self.max_score, current_score + adjustment)
            )
            
            # Add event to history
            event = {
                "type": event_type,
                "timestamp": datetime.now().isoformat(),
                "adjustment": adjustment,
                "new_score": new_score,
                "details": details or {}
            }
            events.append(event)
            
            # Keep only last 100 events
            if len(events) > 100:
                events = events[-100:]
                
            # Update reputation data
            data = {
                "score": str(new_score),
                "last_updated": datetime.now().isoformat(),
                "events": json.dumps(events)
            }
            await redis.hmset(key, data)
            
            return {
                "ip": ip,
                "score": new_score,
                "created_at": rep["created_at"],
                "last_updated": data["last_updated"],
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Error updating reputation for {ip}: {e}")
            return await self.get_reputation(ip)
            
    def get_reputation_level(self, score: float) -> str:
        """Get reputation level based on score"""
        if score <= self.thresholds["block"]:
            return "blocked"
        elif score <= self.thresholds["warn"]:
            return "suspicious"
        elif score <= self.thresholds["verify"]:
            return "neutral"
        elif score <= self.thresholds["trust"]:
            return "trusted"
        else:
            return "highly_trusted"

class RequestCorrelator:
    """Correlate requests to detect attack patterns"""
    
    def __init__(self, redis_prefix: str = "correlation"):
        self.redis_prefix = redis_prefix
        self.cache = SecurityCache(redis_prefix)
        self.metrics = SecurityMetrics()
        
        # Time windows for pattern detection
        self.windows = {
            "short": 300,    # 5 minutes
            "medium": 3600,  # 1 hour
            "long": 86400   # 24 hours
        }
        
        # Pattern thresholds
        self.thresholds = {
            "repeated_violations": 5,
            "distributed_attempts": 10,
            "rapid_requests": 100,
            "concurrent_sessions": 20
        }
        
    async def track_request(
        self,
        request_id: str,
        ip: str,
        path: str,
        method: str,
        status_code: int,
        duration: float,
        user_agent: str,
        session_id: Optional[str] = None
    ) -> None:
        """Track a request for correlation"""
        try:
            timestamp = int(time.time())
            request_data = {
                "id": request_id,
                "ip": ip,
                "path": path,
                "method": method,
                "status_code": status_code,
                "duration": duration,
                "user_agent": user_agent,
                "session_id": session_id,
                "timestamp": timestamp
            }
            
            # Store request data
            await self._store_request(ip, request_data)
            
            # Update pattern tracking
            await self._update_patterns(ip, request_data)
            
        except Exception as e:
            logger.error(f"Error tracking request correlation: {e}")
            
    async def _store_request(self, ip: str, request_data: Dict[str, Any]) -> None:
        """Store request data for correlation"""
        try:
            redis = await get_redis()
            key = f"{self.redis_prefix}:requests:{ip}"
            
            # Store in sorted set with score as timestamp
            await redis.zadd(
                key,
                {json.dumps(request_data): request_data["timestamp"]}
            )
            
            # Trim old data
            max_age = int(time.time()) - self.windows["long"]
            await redis.zremrangebyscore(key, 0, max_age)
            
            # Set expiry
            await redis.expire(key, self.windows["long"])
            
        except RedisError as e:
            logger.error(f"Redis error in request correlation: {e}")
            
    async def _update_patterns(self, ip: str, request_data: Dict[str, Any]) -> None:
        """Update pattern tracking for an IP"""
        try:
            redis = await get_redis()
            timestamp = request_data["timestamp"]
            
            # Track patterns for different windows
            for window_name, window_size in self.windows.items():
                window_key = f"{self.redis_prefix}:patterns:{ip}:{window_name}"
                
                # Get requests in window
                start_time = timestamp - window_size
                key = f"{self.redis_prefix}:requests:{ip}"
                requests = await redis.zrangebyscore(
                    key,
                    start_time,
                    timestamp
                )
                
                # Analyze patterns
                patterns = await self._analyze_patterns(requests)
                
                # Store pattern data
                await redis.hmset(window_key, {
                    "timestamp": timestamp,
                    "patterns": json.dumps(patterns)
                })
                await redis.expire(window_key, window_size)
                
        except RedisError as e:
            logger.error(f"Redis error in pattern tracking: {e}")
            
    async def _analyze_patterns(self, requests: List[str]) -> Dict[str, Any]:
        """Analyze requests for patterns"""
        try:
            requests_data = [json.loads(r) for r in requests]
            patterns = {
                "total_requests": len(requests_data),
                "unique_paths": len(set(r["path"] for r in requests_data)),
                "error_count": sum(1 for r in requests_data if r["status_code"] >= 400),
                "avg_duration": sum(r["duration"] for r in requests_data) / len(requests_data) if requests_data else 0,
                "status_codes": {},
                "methods": {},
                "paths": {},
                "user_agents": {},
                "sessions": set()
            }
            
            # Collect statistics
            for req in requests_data:
                patterns["status_codes"][req["status_code"]] = patterns["status_codes"].get(req["status_code"], 0) + 1
                patterns["methods"][req["method"]] = patterns["methods"].get(req["method"], 0) + 1
                patterns["paths"][req["path"]] = patterns["paths"].get(req["path"], 0) + 1
                patterns["user_agents"][req["user_agent"]] = patterns["user_agents"].get(req["user_agent"], 0) + 1
                if req["session_id"]:
                    patterns["sessions"].add(req["session_id"])
                    
            # Convert sets to lists for JSON serialization
            patterns["sessions"] = list(patterns["sessions"])
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing request patterns: {e}")
            return {}

class SecurityEventLogger:
    """Log and alert on security events"""
    
    def __init__(self, redis_prefix: str = "security_events"):
        self.redis_prefix = redis_prefix
        self.cache = SecurityCache(redis_prefix)
        self.metrics = SecurityMetrics()
        
        # Event severity levels
        self.severity_levels = {
            "debug": 0,
            "info": 1,
            "warning": 2,
            "error": 3,
            "critical": 4
        }
        
        # Alert thresholds
        self.alert_thresholds = {
            "critical": 1,    # Alert immediately
            "error": 5,       # Alert after 5 occurrences
            "warning": 10,    # Alert after 10 occurrences
            "info": 100       # Alert after 100 occurrences
        }
        
    async def log_event(
        self,
        event_type: str,
        severity: str,
        details: Dict[str, Any],
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """Log a security event"""
        try:
            timestamp = datetime.now()
            event_id = self._generate_event_id(event_type, timestamp)
            
            event = {
                "id": event_id,
                "type": event_type,
                "severity": severity,
                "timestamp": timestamp.isoformat(),
                "details": details,
                "source_ip": source_ip,
                "user_id": user_id
            }
            
            # Store event
            await self._store_event(event)
            
            # Update metrics
            self.metrics.record_violation(event_type, severity)
            
            # Check if alert needed
            await self._check_alert_threshold(event)
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")
            return ""
            
    def _generate_event_id(self, event_type: str, timestamp: datetime) -> str:
        """Generate unique event ID"""
        base = f"{event_type}:{timestamp.isoformat()}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]
        
    async def _store_event(self, event: Dict[str, Any]) -> None:
        """Store security event"""
        try:
            redis = await get_redis()
            
            # Store in time-series
            key = f"{self.redis_prefix}:events"
            await redis.zadd(key, {json.dumps(event): time.time()})
            
            # Store by type
            type_key = f"{self.redis_prefix}:type:{event['type']}"
            await redis.zadd(type_key, {json.dumps(event): time.time()})
            
            # Store by severity
            sev_key = f"{self.redis_prefix}:severity:{event['severity']}"
            await redis.zadd(sev_key, {json.dumps(event): time.time()})
            
            # Cleanup old events (keep 30 days)
            max_age = time.time() - (30 * 86400)
            await redis.zremrangebyscore(key, 0, max_age)
            await redis.zremrangebyscore(type_key, 0, max_age)
            await redis.zremrangebyscore(sev_key, 0, max_age)
            
        except RedisError as e:
            logger.error(f"Redis error storing security event: {e}")
            
    async def _check_alert_threshold(self, event: Dict[str, Any]) -> None:
        """Check if alert threshold is reached"""
        try:
            if event["severity"] not in self.alert_thresholds:
                return
                
            threshold = self.alert_thresholds[event["severity"]]
            
            # Count recent events of same type and severity
            redis = await get_redis()
            type_key = f"{self.redis_prefix}:type:{event['type']}"
            count = await redis.zcount(
                type_key,
                time.time() - 3600,  # Last hour
                time.time()
            )
            
            if count >= threshold:
                await self._send_alert(event, count)
                
        except RedisError as e:
            logger.error(f"Redis error checking alert threshold: {e}")
            
    async def _send_alert(self, event: Dict[str, Any], count: int) -> None:
        """Send security alert"""
        try:
            alert = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event["type"],
                "severity": event["severity"],
                "count": count,
                "details": event["details"],
                "source_ip": event["source_ip"],
                "message": f"Security alert: {count} {event['type']} events of severity {event['severity']} in the last hour"
            }
            
            # Log alert
            logger.warning(f"Security Alert: {json.dumps(alert)}")
            
            # Store alert
            redis = await get_redis()
            alert_key = f"{self.redis_prefix}:alerts"
            await redis.zadd(alert_key, {json.dumps(alert): time.time()})
            
            # Implement additional alert notifications here (email, Slack, etc.)
            
        except Exception as e:
            logger.error(f"Error sending security alert: {e}")

class RequestThrottler:
    """Throttle requests based on various criteria"""
    
    def __init__(self, redis_prefix: str = "throttle"):
        self.redis_prefix = redis_prefix
        self.cache = SecurityCache(redis_prefix)
        self.metrics = SecurityMetrics()
        
        # Default throttling rules
        self.default_rules = {
            "global": {
                "rate": 10000,    # requests per minute
                "burst": 1000     # burst capacity
            },
            "per_ip": {
                "rate": 100,      # requests per minute
                "burst": 20       # burst capacity
            },
            "per_endpoint": {
                "rate": 1000,     # requests per minute
                "burst": 100      # burst capacity
            }
        }
        
    async def check_throttle(
        self,
        key: str,
        rule_type: str,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if request should be throttled"""
        try:
            rules = custom_rules or self.default_rules.get(rule_type, self.default_rules["global"])
            
            # Get token bucket
            bucket = await self._get_bucket(key, rule_type, rules)
            
            # Check if request can be processed
            if bucket["tokens"] >= 1:
                # Update bucket
                bucket["tokens"] -= 1
                await self._store_bucket(key, rule_type, bucket)
                return False, None
                
            return True, {
                "rule_type": rule_type,
                "rate": rules["rate"],
                "burst": rules["burst"],
                "reset": bucket["last_update"] + 60  # Reset after 1 minute
            }
            
        except Exception as e:
            logger.error(f"Error checking throttle: {e}")
            return False, None
            
    async def _get_bucket(
        self,
        key: str,
        rule_type: str,
        rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get or create token bucket"""
        try:
            redis = await get_redis()
            bucket_key = f"{self.redis_prefix}:{rule_type}:{key}"
            
            # Get current bucket
            data = await redis.get(bucket_key)
            current_time = int(time.time())
            
            if data:
                bucket = json.loads(data)
                # Refill tokens based on time passed
                time_passed = current_time - bucket["last_update"]
                new_tokens = (time_passed * rules["rate"]) / 60
                bucket["tokens"] = min(
                    rules["burst"],
                    bucket["tokens"] + new_tokens
                )
                bucket["last_update"] = current_time
            else:
                # Create new bucket
                bucket = {
                    "tokens": rules["burst"],
                    "last_update": current_time
                }
                
            return bucket
            
        except RedisError as e:
            logger.error(f"Redis error getting token bucket: {e}")
            return {
                "tokens": 0,
                "last_update": int(time.time())
            }
            
    async def _store_bucket(
        self,
        key: str,
        rule_type: str,
        bucket: Dict[str, Any]
    ) -> None:
        """Store token bucket"""
        try:
            redis = await get_redis()
            bucket_key = f"{self.redis_prefix}:{rule_type}:{key}"
            
            # Store bucket with 1-minute expiry
            await redis.setex(
                bucket_key,
                60,  # 1 minute TTL
                json.dumps(bucket)
            )
            
        except RedisError as e:
            logger.error(f"Redis error storing token bucket: {e}")

class SecurityMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app: FastAPI,
        allowed_hosts: List[str] = None,
        allowed_methods: List[str] = None,
        rate_limit: int = 100,  # requests per minute
        max_body_size: int = 10 * 1024 * 1024,  # 10MB
        block_duration: int = 300,  # 5 minutes
    ):
        """Initialize security middleware with configurable parameters"""
        super().__init__(app)
        self.allowed_hosts = allowed_hosts or ["*"]
        self.allowed_methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "PATCH"]
        self.rate_limit = rate_limit
        self.max_body_size = max_body_size
        self.block_duration = block_duration
        
        # Initialize components
        self.threat_analyzer = ThreatAnalyzer()
        self.rate_limiter = RateLimiter()
        self.reputation_manager = ReputationManager()
        self.correlator = RequestCorrelator()
        self.event_logger = SecurityEventLogger()
        self.throttler = RequestThrottler()
        
        # Redis keys
        self._rate_limit_key = "security:rate_limit:{}"
        self._blocklist_key = "security:blocklist"
        self._violation_key = "security:violations:{}"
        self._ip_range_key = "security:ip_ranges"
        self._cache_key = "security:cache:{}"
        
        # Initialize security context
        self.security_context = SecurityContext()
        
        # Initialize caches
        self._blocked_ips_cache = {}
        self._allowed_ip_ranges = []
        
        # Initialize rate limiter
        self._rate_limiter = RateLimitManager(
            rate_limit=self.rate_limit,
            time_window=60
        )
        
        # Initialize security patterns
        self._path_traversal_pattern = re.compile(r"\.\.\/|\.\.\\")
        self._ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        self._cidr_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$")
        
        # SQL injection patterns
        self._sql_pattern = re.compile(
            r"(?i)(select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from|union\s+select|drop\s+table)",
            re.IGNORECASE
        )
        
        # XSS patterns
        self._xss_pattern = re.compile(
            r"(?i)(<script|javascript:|data:text/html|vbscript:|<img|<svg|onload=|onerror=)",
            re.IGNORECASE
        )
        
        # Command injection patterns
        self._cmd_pattern = re.compile(
            r"(?i)([;&|`\$]|bash\s+-i|nc\s+-e|python\s+-c)",
            re.IGNORECASE
        )
        
        # Suspicious header patterns
        self._suspicious_headers = {
            "x-forwarded-for": re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
            "x-real-ip": re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"),
            "user-agent": re.compile(
                r"(?i)(curl|wget|nikto|sqlmap|arachni|nmap|burp|acunetix)",
                re.IGNORECASE
            )
        }
        
        # Initialize cleanup task
        self._last_cleanup = datetime.now()
        self._cleanup_interval = timedelta(minutes=5)
        
    async def initialize(self) -> None:
        """Initialize security middleware"""
        redis = await get_redis()
        
        # Load IP ranges
        ranges = await redis.smembers(self._ip_range_key)
        self._allowed_ip_ranges = [
            ipaddress.ip_network(cidr) 
            for cidr in ranges 
            if self._cidr_pattern.match(cidr)
        ]
        
        # Initialize security context
        await self.security_context.initialize()
        
    async def cleanup(self) -> None:
        """Cleanup expired entries"""
        if datetime.now() - self._last_cleanup < self._cleanup_interval:
            return
            
        try:
            redis = await get_redis()
            
            # Clear expired rate limits
            keys = await redis.keys(self._rate_limit_key.format("*"))
            for key in keys:
                if not await redis.ttl(key):
                    await redis.delete(key)
                    
            # Clear expired violations
            keys = await redis.keys(self._violation_key.format("*"))
            for key in keys:
                if not await redis.ttl(key):
                    await redis.delete(key)
                    
            # Clear expired blocks
            keys = await redis.keys(self._cache_key.format("*"))
            for key in keys:
                if not await redis.ttl(key):
                    await redis.delete(key)
                    
            # Clear local cache
            self._blocked_ips_cache = {
                ip: (ts, blocked) 
                for ip, (ts, blocked) in self._blocked_ips_cache.items()
                if datetime.now() - ts < timedelta(minutes=5)
            }
            
            self._last_cleanup = datetime.now()
            
        except Exception as e:
            logger.error(f"Error during security cleanup: {e}")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request through security checks"""
        start_time = time.time()
        request_id = self._generate_request_id(request)
        
        try:
            # Initialize security context if not already done
            if not hasattr(self.security_context, '_initialized'):
                await self.security_context.initialize()
                self.security_context._initialized = True
            
            # Get IP reputation
            reputation = await self.reputation_manager.get_reputation(request.client.host)
            reputation_level = self.reputation_manager.get_reputation_level(reputation["score"])
            
            # Check if IP is blocked by reputation
            if reputation_level == "blocked":
                await self.event_logger.log_event(
                    "ip_blocked_by_reputation",
                    "high",
                    {"ip": request.client.host, "score": reputation["score"]},
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_403_FORBIDDEN,
                    content=json.dumps({
                        "error": "Access denied",
                        "detail": "IP address is blocked due to low reputation"
                    }),
                    media_type="application/json"
                )
                
            # Check if IP is already blocked
            if await self._is_ip_blocked(request.client.host):
                await self.event_logger.log_event(
                    "ip_blocked",
                    "high",
                    {"ip": request.client.host},
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_403_FORBIDDEN,
                    content=json.dumps({
                        "error": "Access denied",
                        "detail": "IP address is blocked"
                    }),
                    media_type="application/json"
                )
                
            # Check rate limits with backoff
            is_allowed, rate_limit_info = await self.rate_limiter.check_rate_limit(
                request.client.host
            )
            if not is_allowed:
                await self.event_logger.log_event(
                    "rate_limit_exceeded",
                    "medium",
                    rate_limit_info,
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content=json.dumps({
                        "error": "Rate limit exceeded",
                        "detail": rate_limit_info
                    }),
                    media_type="application/json"
                )
                
            # Check request throttling
            endpoint = f"{request.method}:{request.url.path}"
            is_throttled, throttle_info = await self.throttler.check_throttle(
                endpoint,
                "per_endpoint"
            )
            if is_throttled:
                await self.event_logger.log_event(
                    "request_throttled",
                    "medium",
                    throttle_info,
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content=json.dumps({
                        "error": "Request throttled",
                        "detail": throttle_info
                    }),
                    media_type="application/json"
                )

            # Comprehensive security checks
            if not self._is_host_allowed(request):
                await self.event_logger.log_event(
                    "host_blocked",
                    "high",
                    {"host": request.client.host},
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_403_FORBIDDEN,
                    content=json.dumps({
                        "error": "Access denied",
                        "detail": "Host not allowed"
                    }),
                    media_type="application/json"
                )

            if request.method not in self.allowed_methods:
                await self.event_logger.log_event(
                    "method_not_allowed",
                    "medium",
                    {"method": request.method},
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_403_FORBIDDEN,
                    content=json.dumps({
                        "error": "Method not allowed",
                        "detail": f"Method {request.method} is not allowed"
                    }),
                    media_type="application/json"
                )
            
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_body_size:
                await self.event_logger.log_event(
                    "request_too_large",
                    "medium",
                    {"size": content_length},
                    source_ip=request.client.host
                )
                return Response(
                    status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content=json.dumps({
                        "error": "Request too large",
                        "detail": f"Maximum allowed size is {self.max_body_size} bytes"
                    }),
                    media_type="application/json"
                )

            # Check for path traversal attempts
            if self._path_traversal_pattern.search(request.url.path):
                await self._block_ip(request.client.host)
                raise RateLimitError(
                    error_code=ErrorCode.INVALID_INPUT,
                    message="Path traversal attempt detected",
                    details={"path": request.url.path}
                )
            
            # Check rate limit
            await self._check_rate_limit(request)
            
            # Build security context and analyze request
            context = await self.security_context.build_context(request)
            
            # Read and analyze request content
            body = b""
            async for chunk in request.stream():
                body += chunk
            content = body.decode()
            
            # Perform comprehensive security threat analysis
            content_threats = self.security_context.analyze_request_content(content)
            request_threats = await self._check_security_threats(request)
            
            all_threats = content_threats + request_threats
            if all_threats:
                # Log all threats
                for threat in all_threats:
                    await self.security_context.log_threat(
                        request,
                        threat["type"],
                        threat["severity"],
                        threat["details"]
                    )
                
                # Block IP for high/critical severity threats
                if any(t["severity"] in ("high", "critical") for t in all_threats):
                    await self._block_ip(request.client.host)
                    
                return Response(
                    status_code=HTTP_403_FORBIDDEN,
                    content=json.dumps({
                        "error": "Security violation detected",
                        "threats": [
                            {
                                "type": t["type"],
                                "severity": t["severity"],
                                "message": t["details"]
                            }
                            for t in all_threats
                        ]
                    }),
                    media_type="application/json"
                )
            
            # Process the request
            response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Update metrics
            self.metrics.record_processing_time(duration)
            
            # Track request for correlation
            await self.correlator.track_request(
                request_id=request_id,
                ip=request.client.host,
                path=str(request.url.path),
                method=request.method,
                status_code=response.status_code,
                duration=duration,
                user_agent=request.headers.get("user-agent", ""),
                session_id=request.cookies.get("session")
            )
            
            # Update reputation for successful request
            if response.status_code < 400:
                await self.reputation_manager.update_reputation(
                    request.client.host,
                    "successful_request"
                )
            else:
                await self.reputation_manager.update_reputation(
                    request.client.host,
                    "failed_request",
                    {"status_code": response.status_code}
                )
            
            # Add security headers
            headers = await self.security_context.get_security_headers()
            response.headers.update(headers)
            
            # Add security-related response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-RateLimit-Remaining"] = str(self.rate_limit)  # Implement actual remaining count
            
            return response
            
        except RateLimitError as e:
            logger.warning(f"Security violation from {request.client.host}: {str(e)}")
            await self._handle_violation(request, e)
            return Response(
                content=json.dumps({
                    "error": "Security violation",
                    "detail": str(e),
                    "code": e.error_code
                }),
                status_code=e.status_code,
                media_type="application/json"
            )
        except Exception as e:
            logger.error(f"Security middleware error for {request.client.host}: {str(e)}")
            return Response(
                status_code=HTTP_400_BAD_REQUEST,
                content=json.dumps({"detail": "Bad request"}),
                media_type="application/json"
            )
    
    async def _check_rate_limit(self, request: Request) -> None:
        """Check if request exceeds rate limit"""
        client_ip = request.client.host
        key = self._rate_limit_key.format(client_ip)
        
        redis = await get_redis()
        current = await redis.incr(key)
        
        if current == 1:
            await redis.expire(key, 60)  # Expire after 1 minute
            
        if current > self.rate_limit:
            raise RateLimitError(
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message="Rate limit exceeded",
                details={"limit": self.rate_limit, "window": "1 minute"}
            )
    
    async def _check_security_threats(self, request: Request) -> List[Dict[str, str]]:
        """Check for various security threats in the request and return list of detected threats"""
        threats = []
        # Check if IP is blocked
        if await self._is_ip_blocked(request.client.host):
            threats.append({
                "type": "ip_blocked",
                "severity": "high",
                "details": {"ip": request.client.host}
            })
        # Check request path for traversal attempts
        if self._path_traversal_pattern.search(request.url.path):
            threats.append({
                "type": "path_traversal",
                "severity": "critical",
                "details": {"path": request.url.path}
            })
            await self._block_ip(request.client.host)
        # Check query params for injection attempts
        for param, value in request.query_params.items():
            if self._check_injection_patterns(value):
                threats.append({
                    "type": "injection_attempt",
                    "severity": "high",
                    "details": {"parameter": param, "value": value}
                })
        # Check headers for suspicious patterns
        for header, value in request.headers.items():
            if self._check_header_threats(header, value):
                threats.append({
                    "type": "suspicious_header",
                    "severity": "medium",
                    "details": {"header": header, "value": value}
                })
        return threats
    
    async def _is_ip_blocked(self, ip: str) -> bool:
        """Check if an IP is blocked"""
        if not self._ip_pattern.match(ip):
            return False
        # Check cache first
        if ip in self._blocked_ips_cache:
            ts, blocked = self._blocked_ips_cache[ip]
            # If cache is fresh (5 min), use it
            if datetime.now() - ts < timedelta(minutes=5):
                return blocked
        # Check Redis
        redis = await get_redis()
        is_blocked = await redis.sismember(self._blocklist_key, ip)
        # Update cache
        self._blocked_ips_cache[ip] = (datetime.now(), is_blocked)
        return is_blocked

    async def _block_ip(self, ip: str) -> None:
        """Block an IP address"""
        if not self._ip_pattern.match(ip):
            return
        redis = await get_redis()
        # Add to Redis blocklist
        await redis.sadd(self._blocklist_key, ip)
        # Set block duration
        block_key = self._cache_key.format(f"block:{ip}")
        await redis.setex(block_key, self.block_duration, "1")
        # Update cache
        self._blocked_ips_cache[ip] = (datetime.now(), True)
        # Log block
        logger.warning(f"IP {ip} blocked for {self.block_duration} seconds")

    def _is_ip_in_range(self, ip: str) -> bool:
        """Check if IP is in allowed ranges"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for net in self._allowed_ip_ranges:
                if ip_obj in net:
                    return True
            return False
        except ValueError:
            return False

    def _is_host_allowed(self, request: Request) -> bool:
        """Check if host is allowed"""
        if "*" in self.allowed_hosts:
            return True
        host = request.client.host
        return host in self.allowed_hosts

    def _generate_request_id(self, request: Request) -> str:
        """Generate a unique request ID"""
        import uuid
        return str(uuid.uuid4())

    async def _analyze_request_threats(self, request: Request) -> List[Dict[str, Any]]:
        """Analyze request for threats using ThreatAnalyzer"""
        headers = dict(request.headers)
        path = str(request.url.path)
        query_params = dict(request.query_params)
        try:
            body = await request.body()
            body_str = body.decode() if isinstance(body, bytes) else str(body)
        except Exception:
            body_str = ""
        return self.threat_analyzer.analyze_request(headers, path, query_params, body_str)

    def _check_injection_patterns(self, value: str) -> bool:
        """Check for SQL/XSS/command injection patterns in a value"""
        if not value:
            return False
        for regex in (
            self._sql_pattern,
            self._xss_pattern,
            self._cmd_pattern
        ):
            if regex.search(value):
                return True
        return False

    def _check_header_threats(self, header: str, value: str) -> bool:
        """Check for suspicious header patterns"""
        header_lower = header.lower()
        if header_lower in self._suspicious_headers:
            if self._suspicious_headers[header_lower].search(value):
                return True
        return False

    async def _handle_violation(self, request: Request, error: RateLimitError) -> None:
        """Handle security violation"""
        if not self._ip_pattern.match(request.client.host):
            return
            
        redis = await get_redis()
        violation_key = self._violation_key.format(request.client.host)
        
        # Increment violation count and update details
        violations = await redis.hincrby(violation_key, "count", 1)
        await redis.hset(violation_key, mapping={
            "last_violation": datetime.now().isoformat(),
            "last_error": str(error),
            "path": str(request.url.path),
            "method": request.method
        })
        
        # Block IP if violations exceed threshold
        if violations >= settings.SECURITY_MAX_VIOLATIONS:
            await self._block_ip(request.client.host)
            logger.warning(f"IP {request.client.host} blocked after {violations} violations")
            
        # Set expiry on violation record
        await redis.expire(violation_key, self.block_duration * 2)  # Keep violation history longer than block



from .security_headers import SecurityHeadersMiddleware


def setup_security_headers(app: FastAPI):
    """Attach security headers middleware to the app"""
    app.add_middleware(SecurityHeadersMiddleware)

async def add_ip_range(self, cidr: str) -> bool:
    """Add an IP range to allowed list"""
    if not self._cidr_pattern.match(cidr):
        return False
        
    try:
        # Validate CIDR
        network = ipaddress.ip_network(cidr)
        
        # Add to Redis
        redis = await get_redis()
        await redis.sadd(self._ip_range_key, str(network))
        
        # Update local cache
        if network not in self._allowed_ip_ranges:
            self._allowed_ip_ranges.append(network)
        
        logger.info(f"Added IP range: {network}")
        return True
        
    except ValueError as e:
        logger.error(f"Invalid IP range {cidr}: {e}")
        return False

async def remove_ip_range(self, cidr: str) -> bool:
    """Remove an IP range from allowed list"""
    if not self._cidr_pattern.match(cidr):
        return False
        
    try:
        network = ipaddress.ip_network(cidr)
        
        # Remove from Redis
        redis = await get_redis()
        await redis.srem(self._ip_range_key, str(network))
        
        # Update local cache
        self._allowed_ip_ranges = [
            net for net in self._allowed_ip_ranges 
            if net != network
        ]
        
        logger.info(f"Removed IP range: {network}")
        return True
        
    except ValueError as e:
        logger.error(f"Invalid IP range {cidr}: {e}")
        return False

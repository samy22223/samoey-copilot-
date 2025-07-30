from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import logging
import json
from pydantic import BaseModel
import hashlib
import aioredis
from .ai_security import AISecurityMonitor

logger = logging.getLogger(__name__)

class SecurityMetrics(BaseModel):
    request_count: int = 0
    error_count: int = 0
    blocked_requests: int = 0
    ai_security_events: int = 0
    suspicious_activities: int = 0

class SecurityEvent(BaseModel):
    timestamp: datetime
    event_type: str
    severity: str
    source: str
    details: Dict[str, Any]
    client_ip: Optional[str]
    user_agent: Optional[str]

class SecurityMonitor:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.metrics = SecurityMetrics()
        self.events: List[SecurityEvent] = []
        self.ip_blacklist: set = set()
        self.rate_limits: Dict[str, Dict] = defaultdict(lambda: {"count": 0, "reset_at": datetime.now()})
        self.ai_monitor = AISecurityMonitor()
        self.redis_url = redis_url
        self.redis = None
        
        # Configure thresholds
        self.thresholds = {
            "requests_per_minute": 100,
            "errors_per_minute": 10,
            "suspicious_threshold": 5,
            "block_threshold": 10
        }

    async def initialize(self):
        """Initialize Redis connection and start background tasks."""
        self.redis = await aioredis.create_redis_pool(self.redis_url)
        asyncio.create_task(self._cleanup_old_data())

    async def monitor_request(self, request: Any, response: Any) -> bool:
        """Monitor and analyze a request-response pair."""
        client_ip = request.client.host
        
        # Check if IP is blacklisted
        if client_ip in self.ip_blacklist:
            return False
        
        # Rate limiting
        if not await self._check_rate_limit(client_ip):
            return False
        
        # Create security event
        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type="request",
            severity="info",
            source="monitor",
            details={
                "method": request.method,
                "path": str(request.url),
                "status_code": response.status_code,
                "response_time": response.headers.get("X-Response-Time")
            },
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent")
        )
        
        # Store event
        await self._store_event(event)
        
        # Update metrics
        self.metrics.request_count += 1
        if response.status_code >= 400:
            self.metrics.error_count += 1
        
        # Analyze for suspicious activity
        if await self._analyze_suspicious_activity(client_ip):
            return False
        
        return True

    async def monitor_ai_request(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor and analyze AI-related requests."""
        # Analyze prompt security
        security_analysis = self.ai_monitor.analyze_prompt(prompt, context)
        
        if not security_analysis["safe"]:
            self.metrics.ai_security_events += 1
            
            event = SecurityEvent(
                timestamp=datetime.now(),
                event_type="ai_security",
                severity="high",
                source="ai_monitor",
                details={
                    "threats": security_analysis["threats"],
                    "prompt_signature": security_analysis["signature"]
                },
                client_ip=context.get("client_ip"),
                user_agent=context.get("user_agent")
            )
            
            await self._store_event(event)
        
        return security_analysis

    async def _store_event(self, event: SecurityEvent):
        """Store security event in Redis."""
        if self.redis:
            key = f"security:event:{event.timestamp.isoformat()}"
            await self.redis.set(
                key,
                json.dumps(event.dict()),
                expire=86400  # Store for 24 hours
            )
        self.events.append(event)

    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check and enforce rate limits."""
        now = datetime.now()
        rate_info = self.rate_limits[client_ip]
        
        if now > rate_info["reset_at"]:
            rate_info["count"] = 0
            rate_info["reset_at"] = now + timedelta(minutes=1)
        
        rate_info["count"] += 1
        return rate_info["count"] <= self.thresholds["requests_per_minute"]

    async def _analyze_suspicious_activity(self, client_ip: str) -> bool:
        """Analyze for suspicious activity patterns."""
        if self.redis:
            key = f"security:suspicious:{client_ip}"
            count = await self.redis.incr(key)
            await self.redis.expire(key, 3600)  # Expire after 1 hour
            
            if count > self.thresholds["suspicious_threshold"]:
                self.metrics.suspicious_activities += 1
                
            if count > self.thresholds["block_threshold"]:
                self.ip_blacklist.add(client_ip)
                self.metrics.blocked_requests += 1
                return True
        
        return False

    async def _cleanup_old_data(self):
        """Cleanup old security data periodically."""
        while True:
            try:
                # Remove old events
                cutoff = datetime.now() - timedelta(days=1)
                self.events = [e for e in self.events if e.timestamp > cutoff]
                
                # Reset metrics
                if datetime.now().minute == 0:
                    self.metrics = SecurityMetrics()
                
            except Exception as e:
                logger.error(f"Error in cleanup: {e}")
            
            await asyncio.sleep(60)  # Run every minute

    async def get_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        ai_report = self.ai_monitor.get_security_report()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.dict(),
            "ai_security": ai_report,
            "blacklisted_ips": len(self.ip_blacklist),
            "recent_events": [e.dict() for e in self.events[-10:]],
            "threat_level": self._calculate_threat_level()
        }

    def _calculate_threat_level(self) -> str:
        """Calculate overall threat level."""
        if self.metrics.ai_security_events > 5 or self.metrics.blocked_requests > 10:
            return "CRITICAL"
        elif self.metrics.suspicious_activities > 10:
            return "HIGH"
        elif self.metrics.error_count > self.thresholds["errors_per_minute"]:
            return "MEDIUM"
        return "LOW"

from typing import Dict, List, Optional
import re
import json
from datetime import datetime
import aioredis
from fastapi import HTTPException, Request
from prometheus_client import Counter, Histogram
import logging
from ..core.security_settings import security_settings

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
THREAT_DETECTIONS = Counter('threat_detections_total', 'Total threats detected', ['threat_type'])
AI_SECURITY_EVENTS = Counter('ai_security_events_total', 'Total AI security events', ['event_type'])
MODEL_ACCESS_TIME = Histogram('model_access_duration_seconds', 'Model access duration')

class AdvancedSecurity:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.threat_patterns = {
            'sql_injection': r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b.*\b(FROM|INTO|TABLE)\b)',
            'xss': r'(<script.*?>.*?</script>|javascript:|data:text/html)',
            'path_traversal': r'(\.\./|\.\./\./|~/)',
            'command_injection': r'(;\s*[\w\d]+\s+|`.*?`|\|\s*\w+)',
            'prompt_injection': r'(ignore.*instructions|bypass.*security|override.*system)',
            'sensitive_data': r'(password|credit.?card|ssn|social.?security)',
        }
        self.ai_threat_patterns = {
            'model_manipulation': r'(change.*model.*behavior|override.*model|manipulate.*output)',
            'training_injection': r'(poison.*training|manipulate.*learning|corrupt.*model)',
            'data_extraction': r'(extract.*data|leak.*information|bypass.*filter)',
            'resource_abuse': r'(infinite.*loop|consume.*resources|overflow.*memory)',
        }

    async def initialize(self):
        """Initialize Redis connection"""
        self.redis = await aioredis.create_redis_pool(
            f'redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}',
            db=security_settings.REDIS_SECURITY_DB
        )

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()

    async def analyze_request(self, request: Request) -> Dict[str, List[str]]:
        """Analyze request for security threats"""
        threats = {'general': [], 'ai_specific': []}
        
        # Get request components
        headers = dict(request.headers)
        params = dict(request.query_params)
        
        # Check body if available
        body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.json()
            except:
                body = None

        # Analyze components
        await self._analyze_components(headers, threats)
        await self._analyze_components(params, threats)
        if body:
            await self._analyze_components(body, threats)

        return threats

    async def _analyze_components(self, data: Dict, threats: Dict[str, List[str]]):
        """Analyze components for threats"""
        str_data = json.dumps(data)
        
        # Check general threats
        for threat_type, pattern in self.threat_patterns.items():
            if re.search(pattern, str_data, re.IGNORECASE):
                threats['general'].append(threat_type)
                THREAT_DETECTIONS.labels(threat_type=threat_type).inc()

        # Check AI-specific threats
        for threat_type, pattern in self.ai_threat_patterns.items():
            if re.search(pattern, str_data, re.IGNORECASE):
                threats['ai_specific'].append(threat_type)
                AI_SECURITY_EVENTS.labels(event_type=threat_type).inc()

    async def analyze_ai_input(self, input_data: Dict) -> Dict[str, List[str]]:
        """Analyze AI input for security threats"""
        threats = []
        str_input = json.dumps(input_data)

        # Check for AI-specific threats
        for threat_type, pattern in self.ai_threat_patterns.items():
            if re.search(pattern, str_input, re.IGNORECASE):
                threats.append(threat_type)
                await self._log_ai_security_event(threat_type, input_data)

        return {'detected_threats': threats}

    async def _log_ai_security_event(self, event_type: str, details: Dict):
        """Log AI security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details
        }
        await self.redis.lpush('security:ai:events', json.dumps(event))
        await self.redis.ltrim('security:ai:events', 0, 999)  # Keep last 1000 events

    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check rate limit for a key"""
        current = await self.redis.incr(f'ratelimit:{key}')
        if current == 1:
            await self.redis.expire(f'ratelimit:{key}', window)
        return current <= limit

    async def get_security_status(self) -> Dict:
        """Get current security status"""
        return {
            'threats_detected': await self.redis.get('security:threats:total') or 0,
            'ai_security_events': await self.redis.get('security:ai:events:total') or 0,
            'blocked_requests': await self.redis.get('security:blocked:total') or 0,
            'active_defenses': await self.redis.smembers('security:active_defenses')
        }

    def validate_ai_response(self, response: Dict) -> bool:
        """Validate AI response for security issues"""
        str_response = json.dumps(response)
        
        # Check for sensitive data leakage
        if re.search(self.threat_patterns['sensitive_data'], str_response, re.IGNORECASE):
            logger.warning("Sensitive data detected in AI response")
            return False

        # Add more validation rules as needed
        return True

    async def update_defense_rules(self, rules: Dict):
        """Update defense rules"""
        await self.redis.delete('security:defense:rules')
        await self.redis.hmset('security:defense:rules', rules)

    async def get_defense_rules(self) -> Dict:
        """Get current defense rules"""
        return await self.redis.hgetall('security:defense:rules')

advanced_security = AdvancedSecurity()

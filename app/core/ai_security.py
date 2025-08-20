from typing import Dict, List, Optional
import re
import json
from datetime import datetime
import aioredis
from fastapi import HTTPException
import logging
from prometheus_client import Counter, Histogram
from ..core.security_settings import security_settings

# Setup logging
logger = logging.getLogger(__name__)

# Prometheus metrics
AI_MODEL_CALLS = Counter('ai_model_calls_total', 'Total AI model calls', ['model_name'])
AI_MODEL_ERRORS = Counter('ai_model_errors_total', 'Total AI model errors', ['error_type'])
AI_MODEL_LATENCY = Histogram('ai_model_latency_seconds', 'AI model latency')

class AISecurityManager:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.prompt_injection_patterns = [
            r'ignore.*previous.*instructions',
            r'bypass.*security',
            r'override.*system',
            r'change.*behavior',
            r'disable.*protection',
            r'remove.*restriction',
        ]
        self.sensitive_data_patterns = [
            r'\b\d{16}\b',  # Credit card numbers
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'password|secret|key|token|credential',  # Sensitive keywords
        ]
        self.model_abuse_patterns = [
            r'infinite.*loop',
            r'recursion',
            r'fork.*bomb',
            r'resource.*exhaustion',
        ]

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

    async def validate_ai_request(self, request_data: Dict) -> Dict[str, List[str]]:
        """Validate AI request for security issues"""
        threats = []
        
        # Convert request data to string for pattern matching
        request_str = json.dumps(request_data)
        
        # Check for prompt injection
        if any(re.search(pattern, request_str, re.IGNORECASE) 
               for pattern in self.prompt_injection_patterns):
            threats.append('prompt_injection')
        
        # Check for sensitive data
        if any(re.search(pattern, request_str, re.IGNORECASE) 
               for pattern in self.sensitive_data_patterns):
            threats.append('sensitive_data')
        
        # Check for model abuse
        if any(re.search(pattern, request_str, re.IGNORECASE) 
               for pattern in self.model_abuse_patterns):
            threats.append('model_abuse')
        
        if threats:
            await self._log_ai_security_event('request_validation', {
                'threats': threats,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return {'detected_threats': threats}

    async def sanitize_ai_input(self, input_data: Dict) -> Dict:
        """Sanitize AI input to remove potential threats"""
        sanitized = json.loads(json.dumps(input_data))  # Deep copy
        
        # Remove potentially dangerous patterns
        if isinstance(sanitized.get('prompt'), str):
            for pattern in self.prompt_injection_patterns:
                sanitized['prompt'] = re.sub(
                    pattern, '[FILTERED]', 
                    sanitized['prompt'], 
                    flags=re.IGNORECASE
                )
        
        return sanitized

    async def validate_ai_response(self, response_data: Dict) -> bool:
        """Validate AI response for security issues"""
        response_str = json.dumps(response_data)
        
        # Check for sensitive data in response
        if any(re.search(pattern, response_str, re.IGNORECASE) 
               for pattern in self.sensitive_data_patterns):
            await self._log_ai_security_event('response_validation', {
                'issue': 'sensitive_data_leak',
                'timestamp': datetime.utcnow().isoformat()
            })
            return False
        
        return True

    async def track_model_usage(self, model_name: str, duration: float, success: bool):
        """Track AI model usage metrics"""
        AI_MODEL_CALLS.labels(model_name=model_name).inc()
        AI_MODEL_LATENCY.observe(duration)
        
        if not success:
            AI_MODEL_ERRORS.labels(error_type='model_error').inc()
        
        # Store in Redis for real-time monitoring
        await self.redis.hincrby(f'ai:model:usage:{model_name}', 'calls', 1)
        await self.redis.hincrbyfloat(
            f'ai:model:usage:{model_name}', 
            'total_duration', 
            duration
        )

    async def _log_ai_security_event(self, event_type: str, details: Dict):
        """Log AI security event"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details
        }
        
        # Store in Redis
        await self.redis.lpush('ai:security:events', json.dumps(event))
        await self.redis.ltrim('ai:security:events', 0, 999)  # Keep last 1000 events
        
        # Update metrics
        await self.redis.hincrby('ai:security:metrics', event_type, 1)

    async def get_ai_security_status(self) -> Dict:
        """Get AI security status"""
        return {
            'events': await self.redis.lrange('ai:security:events', 0, 9),
            'metrics': await self.redis.hgetall('ai:security:metrics'),
            'model_usage': {
                model: await self.redis.hgetall(f'ai:model:usage:{model}')
                for model in await self.redis.smembers('ai:models')
            }
        }

    def get_security_headers(self) -> Dict[str, str]:
        """Get AI-specific security headers"""
        return {
            'X-AI-Security': 'enabled',
            'X-Model-Protection': 'active',
            'X-Prompt-Validation': 'strict',
            'X-Response-Validation': 'enabled'
        }

ai_security_manager = AISecurityManager()

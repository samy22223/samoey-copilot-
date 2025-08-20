from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import re
from fastapi import Request
from ..core.redis import get_redis

class SecurityContext:
    """Manages security context and metrics for request analysis"""
    
    def __init__(self):
        self.metrics_key = "security:metrics"
        self.security_patterns = {
            'sql_injection': [
                r"(?i)(?:select|insert|update|delete|drop|union|into|load_file).*(?:from|into|where)",
                r"(?i)(?:--|#|/\*|\*/|\{|\}|'|\")",
                r"(?i)(?:waitfor|benchmark|sleep)\s*\(",
            ],
            'command_injection': [
                r"(?i)(?:system|exec|eval|os\.|subprocess)",
                r"(?i)(?:\/bin\/(?:ba)?sh|\||>|<|\$\(|\`)",
                r"(?:[;&|`\n]|$\()",
            ],
            'path_traversal': [
                r"(?i)(?:\.\.\/|\.\.\\)",
                r"(?i)(?:\/etc\/(?:passwd|shadow|group)|\/var\/log)",
            ],
            'xss': [
                r"(?i)(?:<script.*?>|<.*?onload=|<.*?onclick=)",
                r"(?i)(?:javascript:|data:text\/html|vbscript:)",
            ],
            'sensitive_data': [
                r"(?i)(?:password|secret|token|key).*?[=:]\s*['\"]?[\w-]+",
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit card pattern
            ],
            'api_patterns': [
                r"(?i)(?:api[_-]?key|access[_-]?token|secret[_-]?key)",
                r"(?i)bearer\s+[a-zA-Z0-9\-\._~\+\/]+=*",
            ],
            'model_attack': [
                r"(?i)(?:model\.load_state_dict|model\.parameters|weights?\.h5)",
                r"(?i)(?:checkpoint|savepoint|restore|backup)\s*(?:from|to|path)",
            ],
            'rate_limiting': [
                r"(?i)(?:ddos|flood|spam|brute[-\s]?force)",
                r"(?:\d+\s*requests?\s*(?:per|\/)\s*(?:second|minute|hour))",
            ]
        }

    async def initialize(self):
        """Initialize security context and metrics"""
        await self._init_security_metrics()

    async def _init_security_metrics(self):
        """Initialize security metrics in Redis"""
        redis = await get_redis()
        default_metrics = {
            "total_requests": 0,
            "blocked_requests": 0,
            "ai_requests": 0,
            "violations": 0,
            "model_attacks": 0,
            "injection_attempts": 0,
            "data_exfiltration": 0,
            "authentication_bypass": 0,
            "last_update": datetime.now().isoformat()
        }
        if not await redis.exists(self.metrics_key):
            await redis.hset(self.metrics_key, mapping=default_metrics)

    def analyze_request_content(self, content: str) -> List[str]:
        """Analyze request content for security patterns"""
        detected_threats = []
        for threat_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    detected_threats.append(threat_type)
                    break
        return detected_threats

    async def update_metrics(self, metrics_update: Dict[str, Any]):
        """Update security metrics in Redis"""
        redis = await get_redis()
        await redis.hincrby(self.metrics_key, "total_requests", 1)
        for key, value in metrics_update.items():
            if isinstance(value, int):
                await redis.hincrby(self.metrics_key, key, value)
            else:
                await redis.hset(self.metrics_key, key, value)
        await redis.hset(self.metrics_key, "last_update", datetime.now().isoformat())

    async def build_context(self, request: Request) -> Dict[str, Any]:
        """Build security context from request"""
        redis = await get_redis()
        return {
            "request_count": await redis.hincrby(f'security:requests:{request.client.host}', 'count', 1),
            "previous_violations": await redis.hget(f'security:violations:{request.client.host}', 'total') or 0,
            "method": request.method,
            "path": request.url.path,
            "headers": dict(request.headers)
        }

    async def log_threat(self, request: Request, detected_threats: List[str]):
        """Log detected security threats"""
        redis = await get_redis()
        threat_details = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": request.client.host,
            "method": request.method,
            "path": str(request.url.path),
            "detected_threats": detected_threats
        }
        
        # Update violation metrics
        violations_key = f'security:violations:{request.client.host}'
        await redis.hincrby(violations_key, "total", len(detected_threats))
        await redis.hset(violations_key, "last_violation", json.dumps(threat_details))
        
        # Update general metrics
        metrics = {
            "blocked_requests": 1,
            "violations": len(detected_threats)
        }
        await self.update_metrics(metrics)

    async def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for response"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

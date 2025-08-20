from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict
import json
import redis
import time
from datetime import datetime

class AISecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client: redis.Redis):
        super().__init__(app)
        self.redis = redis_client
        self.rate_limits = {
            "default": {"rate": 100, "per": 60},  # 100 requests per minute
            "ai_endpoints": {"rate": 50, "per": 60},  # 50 AI requests per minute
            "security_critical": {"rate": 20, "per": 60}  # 20 security-critical requests per minute
        }

    async def dispatch(self, request: Request, call_next):
        # Implement rate limiting
        await self._check_rate_limit(request)
        
        # Check for potential threats
        await self._check_threat_patterns(request)
        
        # Apply AI-specific security checks
        await self._apply_ai_security_checks(request)
        
        # Track metrics
        await self._track_security_metrics(request)
        
        response = await call_next(request)
        
        # Add AI security response headers
        response.headers.update(await self._get_ai_security_headers())
        
        return response

    async def _check_rate_limit(self, request: Request):
        client_ip = request.client.host
        path = request.url.path
        
        # Determine rate limit category
        category = self._get_rate_limit_category(path)
        limits = self.rate_limits[category]
        
        # Check rate limit
        key = f"ratelimit:{category}:{client_ip}"
        current = self.redis.get(key)
        
        if current and int(current) >= limits["rate"]:
            self._record_security_event(
                "rate_limit_exceeded",
                {"ip": client_ip, "path": path, "category": category}
            )
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        
        # Update rate limit counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, limits["per"])
        pipe.execute()

    def _get_rate_limit_category(self, path: str) -> str:
        if path.startswith("/api/ai/") or path.startswith("/api/ml/"):
            return "ai_endpoints"
        elif path.startswith("/api/security/"):
            return "security_critical"
        return "default"

    async def _check_threat_patterns(self, request: Request):
        # Get request body if available
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                body = None

        # Check for suspicious patterns
        await self._analyze_request_patterns(request, body)

    async def _analyze_request_patterns(self, request: Request, body: Optional[Dict] = None):
        threats = []
        
        # Check headers for suspicious patterns
        for header, value in request.headers.items():
            if self._contains_threat_pattern(value):
                threats.append(f"Suspicious header pattern: {header}")

        # Check query parameters
        for param, value in request.query_params.items():
            if self._contains_threat_pattern(value):
                threats.append(f"Suspicious query parameter: {param}")

        # Check body content if available
        if body:
            if isinstance(body, dict):
                for key, value in body.items():
                    if self._contains_threat_pattern(str(value)):
                        threats.append(f"Suspicious body content: {key}")

        if threats:
            self._record_security_event(
                "threat_pattern_detected",
                {
                    "ip": request.client.host,
                    "path": request.url.path,
                    "threats": threats
                }
            )
            raise HTTPException(status_code=403, detail="Suspicious request pattern detected")

    def _contains_threat_pattern(self, value: str) -> bool:
        # Add your threat pattern detection logic here
        threat_patterns = [
            "SELECT.*FROM",  # SQL injection
            "<script.*>",    # XSS
            "eval\\(",      # Code injection
            "system\\(",    # Command injection
            "\\{\\{.*\\}\\}"  # Template injection
        ]
        
        return any(pattern in value for pattern in threat_patterns)

    async def _apply_ai_security_checks(self, request: Request):
        if request.url.path.startswith(("/api/ai/", "/api/ml/")):
            # Validate AI-specific headers
            required_headers = ["X-API-Key", "X-Request-ID"]
            for header in required_headers:
                if header not in request.headers:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Missing required AI security header: {header}"
                    )

            # Check for AI-specific threats
            await self._check_ai_threats(request)

    async def _check_ai_threats(self, request: Request):
        # Implement AI-specific threat detection
        body = None
        try:
            body = await request.json()
        except:
            return

        if body:
            # Check for prompt injection attempts
            if self._detect_prompt_injection(body):
                self._record_security_event(
                    "prompt_injection_attempt",
                    {"ip": request.client.host, "path": request.url.path}
                )
                raise HTTPException(
                    status_code=403,
                    detail="Potential prompt injection detected"
                )

    def _detect_prompt_injection(self, body: Dict) -> bool:
        # Add your prompt injection detection logic here
        suspicious_patterns = [
            "ignore previous instructions",
            "bypass security",
            "override system",
            "ignore rules"
        ]
        
        content = json.dumps(body).lower()
        return any(pattern in content for pattern in suspicious_patterns)

    async def _track_security_metrics(self, request: Request):
        # Update request metrics
        self.redis.incr("security:metrics:request_count")
        
        # Track endpoint usage
        path_key = f"security:endpoint:{request.url.path}"
        self.redis.incr(path_key)
        self.redis.expire(path_key, 86400)  # Expire after 24 hours

    def _record_security_event(self, event_type: str, details: Dict):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "details": details
        }
        
        # Store event in Redis
        self.redis.lpush("security:events", json.dumps(event))
        self.redis.ltrim("security:events", 0, 999)  # Keep last 1000 events
        
        # Update metrics
        self.redis.incr(f"security:metrics:{event_type}")
        self.redis.expire(f"security:metrics:{event_type}", 86400)

    async def _get_ai_security_headers(self) -> Dict[str, str]:
        return {
            "X-AI-Security-Version": "2.0",
            "X-AI-Protection-Mode": "strict",
            "X-AI-Threat-Detection": "enabled",
            "X-Model-Access-Control": "restricted",
            "X-Prompt-Validation": "enabled"
        }

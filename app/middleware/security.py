import re
import json
from typing import Dict, List, Optional, Set
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for input validation and threat detection"""

    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()

        # Common attack patterns
        self.sql_injection_patterns = [
            r'(union.*select.*from)',
            r'(insert.*into.*values)',
            r'(update.*set)',
            r'(delete.*from)',
            r'(drop.*table)',
            r'(exec\()',
            r'(xp_cmdshell)',
            r'(sp_oacreate)',
            r'(;|--|\/\*|\*\/)',
            r'(\bor\b.*\b\d+\b.*\b=\b)',
            r'(\bselect\b.*\bfrom\b)',
        ]

        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'vbscript:',
            r'onload\s*=',
            r'onerror\s*=',
            r'onclick\s*=',
            r'onmouseover\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'eval\s*\(',
            r'document\.cookie',
            r'document\.write',
            r'window\.location',
            r'<.*?on\w+\s*=',
        ]

        self.path_traversal_patterns = [
            r'\.\.\/',
            r'\.\.\\',
            r'~\/',
            r'~\\',
            r'%2e%2e%2f',
            r'%2e%2e\\',
            r'..%2f',
            r'..%5c',
        ]

        self.command_injection_patterns = [
            r'(\||&|;|\$|\(|\)|`|>|<)',
            r'(nc\s+|netcat\s+)',
            r'(telnet\s+)',
            r'(wget\s+|curl\s+)',
            r'(ping\s+)',
            r'(nslookup\s+|dig\s+)',
            r'(whoami\s+|id\s+)',
            r'(uname\s+|hostname\s+)',
        ]

        # Rate limiting storage
        self.request_counts: Dict[str, List[float]] = {}
        self.blocked_ips: Set[str] = set()

        # Size limits
        self.max_request_size = settings.MAX_UPLOAD_SIZE
        self.max_query_length = 2048
        self.max_header_length = 8192

    async def dispatch(self, request: Request, call_next):
        """Process each request through security checks"""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "IP address is blocked due to suspicious activity"}
            )

        # Rate limiting
        if not await self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )

        # Request size validation
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(f"Request too large from IP: {client_ip}, size: {content_length}")
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"detail": "Request body too large"}
            )

        # Header validation
        if not await self._validate_headers(request):
            logger.warning(f"Invalid headers from IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request headers"}
            )

        # Path validation
        if not await self._validate_path(request.url.path):
            logger.warning(f"Invalid path access attempt from IP: {client_ip}, path: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request path"}
            )

        # Query parameter validation
        if not await self._validate_query_params(request):
            logger.warning(f"Malicious query parameters from IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Malicious content detected in query parameters"}
            )

        # Check user agent for suspicious patterns
        if not await self._validate_user_agent(user_agent, client_ip):
            logger.warning(f"Suspicious user agent from IP: {client_ip}, UA: {user_agent}")

        # For POST/PUT/PATCH requests, validate body content
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON for validation
                    try:
                        json_data = json.loads(body.decode('utf-8'))
                        if not await self._validate_json_input(json_data, client_ip):
                            logger.warning(f"Malicious JSON content from IP: {client_ip}")
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Malicious content detected in request body"}
                            )
                    except json.JSONDecodeError:
                        # Not JSON, validate as raw text
                        if not await self._validate_raw_input(body.decode('utf-8', errors='ignore'), client_ip):
                            logger.warning(f"Malicious raw content from IP: {client_ip}")
                            return JSONResponse(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                content={"detail": "Malicious content detected in request body"}
                            )
            except Exception as e:
                logger.error(f"Error reading request body: {e}")

        # Add security headers
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' wss: https:; frame-ancestors 'none';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers (reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"

    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        import time

        current_time = time.time()
        window_start = current_time - settings.RATE_LIMIT_WINDOW

        # Clean old entries
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if timestamp > window_start
            ]
        else:
            self.request_counts[client_ip] = []

        # Check if limit exceeded
        if len(self.request_counts[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
            return False

        # Add current request
        self.request_counts[client_ip].append(current_time)
        return True

    async def _validate_headers(self, request: Request) -> bool:
        """Validate request headers for security"""
        # Check for suspicious headers
        suspicious_headers = [
            "x-proxy-user-ip",
            "x-forwarded-server",
            "via",  # Often used in proxy attacks
        ]

        for header in suspicious_headers:
            if header in request.headers:
                value = request.headers[header].lower()
                if any(suspicious in value for suspicious in ["proxy", "tor", "vpn"]):
                    return False

        # Check header lengths
        for name, value in request.headers.items():
            if len(value) > self.max_header_length:
                return False

        return True

    async def _validate_path(self, path: str) -> bool:
        """Validate request path for traversal attacks"""
        # Check for path traversal patterns
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False

        # Check for suspicious file extensions
        suspicious_extensions = [".php", ".asp", ".jsp", ".exe", ".bat", ".cmd", ".sh"]
        for ext in suspicious_extensions:
            if path.lower().endswith(ext):
                return False

        return True

    async def _validate_query_params(self, request: Request) -> bool:
        """Validate query parameters for injection attacks"""
        query_string = str(request.query_params)

        # Check query length
        if len(query_string) > self.max_query_length:
            return False

        # Check for various injection patterns
        all_patterns = (
            self.sql_injection_patterns +
            self.xss_patterns +
            self.command_injection_patterns
        )

        for pattern in all_patterns:
            if re.search(pattern, query_string, re.IGNORECASE):
                return False

        return True

    async def _validate_user_agent(self, user_agent: str, client_ip: str) -> bool:
        """Validate user agent string"""
        if not user_agent or len(user_agent.strip()) == 0:
            # Empty user agent is suspicious
            return False

        # Check for known malicious user agents
        malicious_patterns = [
            "sqlmap", "nikto", "nmap", "masscan", "zgrab",
            "curl/", "wget/", "python-requests", "bot", "spider",
            "scanner", "crawler", "grabber"
        ]

        user_agent_lower = user_agent.lower()
        for pattern in malicious_patterns:
            if pattern in user_agent_lower:
                logger.info(f"Known tool user agent detected: {user_agent} from IP: {client_ip}")
                return False

        return True

    async def _validate_json_input(self, data: Dict, client_ip: str) -> bool:
        """Validate JSON input for malicious content"""
        # Convert JSON to string for pattern matching
        json_str = json.dumps(data, separators=(',', ':'))

        # Check for various injection patterns
        all_patterns = (
            self.sql_injection_patterns +
            self.xss_patterns +
            self.command_injection_patterns
        )

        for pattern in all_patterns:
            if re.search(pattern, json_str, re.IGNORECASE):
                return False

        # Check for nested objects that could cause DoS
        if self._check_json_depth(data) > 10:
            return False

        return True

    async def _validate_raw_input(self, input_text: str, client_ip: str) -> bool:
        """Validate raw input text for malicious content"""
        # Check for various injection patterns
        all_patterns = (
            self.sql_injection_patterns +
            self.xss_patterns +
            self.command_injection_patterns
        )

        for pattern in all_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                return False

        return True

    def _check_json_depth(self, obj, depth=0) -> int:
        """Check JSON object depth to prevent DoS attacks"""
        if depth > 10:
            return depth

        if isinstance(obj, dict):
            if not obj:
                return depth
            return max(self._check_json_depth(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return depth
            return max(self._check_json_depth(item, depth + 1) for item in obj)

        return depth

# Function to setup security middleware
def setup_security_middleware(app):
    """Setup security middleware for FastAPI application"""
    app.add_middleware(SecurityMiddleware)
    return app

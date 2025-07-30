from fastapi import FastAPI
from prometheus_client import Counter, Histogram
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
import os

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_request_count",
    "HTTP Request Count",
    ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP Request Latency",
    ["method", "endpoint"]
)

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Record request duration
        duration = time.time() - start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Record request count
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        return response

def setup_monitoring(app: FastAPI):
    """Set up monitoring with Sentry and Prometheus."""
    # Initialize Sentry
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0,
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    # Add Prometheus monitoring middleware
    app.add_middleware(MonitoringMiddleware)

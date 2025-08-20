from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import logging
import time

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # Calculate request processing time
        process_time = time.time() - start_time
        
        # Log request details
        logging.info(
            f"Method: {request.method} Path: {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.2f}s "
            f"Client: {request.client.host if request.client else 'Unknown'}"
        )
        
        return response

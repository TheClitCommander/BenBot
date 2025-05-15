"""Performance monitoring middleware for FastAPI."""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor and log request performance.
    
    This middleware adds timing information to response headers.
    """

    def __init__(self, app: ASGIApp, log_threshold_ms: float = 500):
        """Initialize the middleware.
        
        Args:
            app: The ASGI app
            log_threshold_ms: Threshold in milliseconds to log slow requests
        """
        super().__init__(app)
        self.log_threshold_ms = log_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add performance metrics.
        
        Args:
            request: The incoming request
            call_next: The next request handler
            
        Returns:
            The response with added performance headers
        """
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        process_time_ms = process_time * 1000
        
        # Add timing headers
        response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
        
        # Log slow requests
        if process_time_ms > self.log_threshold_ms:
            print(f"SLOW REQUEST: {request.method} {request.url.path} took {process_time_ms:.2f}ms")
        
        return response


def add_performance_middleware(app: FastAPI, log_threshold_ms: float = 500) -> None:
    """Add the performance middleware to a FastAPI app.
    
    Args:
        app: The FastAPI application
        log_threshold_ms: Threshold in milliseconds to log slow requests
    """
    app.add_middleware(PerformanceMiddleware, log_threshold_ms=log_threshold_ms) 
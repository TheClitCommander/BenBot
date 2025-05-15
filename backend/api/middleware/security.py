"""Security middleware for FastAPI."""

import os
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from fastapi.security.api_key import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and add security headers.
        
        Args:
            request: The incoming request
            call_next: The next request handler
            
        Returns:
            The response with added security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), interest-cohort=()"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware.
    
    This is a basic implementation. For production, use a Redis-based solution.
    """

    def __init__(
        self, 
        app: ASGIApp, 
        requests_per_minute: int = 60,
        exclude_paths: Optional[list[str]] = None
    ):
        """Initialize the middleware.
        
        Args:
            app: The ASGI app
            requests_per_minute: Maximum requests per minute per IP
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc"]
        self.requests = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request with rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next request handler
            
        Returns:
            The response or a rate limit error
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
            
        # In production, use X-Forwarded-For with validation or other reliable client ID
        client_ip = request.client.host if request.client else "unknown"
        current_time = int(time.time() / 60)  # Current minute
        
        # Reset counter for new minute
        if client_ip in self.requests and self.requests[client_ip][0] < current_time:
            self.requests[client_ip] = [current_time, 1]
        else:
            # Initialize or increment counter
            if client_ip not in self.requests:
                self.requests[client_ip] = [current_time, 1]
            else:
                self.requests[client_ip][1] += 1
        
        # Check if rate limit exceeded
        if self.requests[client_ip][1] > self.requests_per_minute:
            return Response(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                media_type="application/json"
            )
        
        return await call_next(request)


def setup_api_key_auth(app: FastAPI) -> None:
    """Set up API key authentication.
    
    Args:
        app: The FastAPI application
    """
    API_KEY = os.environ.get("API_KEY", "")
    API_KEY_NAME = "X-API-Key"
    
    api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
    
    @app.middleware("http")
    async def api_key_middleware(request: Request, call_next: Callable) -> Response:
        # Skip API key check for public endpoints
        public_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Check API key
        api_key = request.headers.get(API_KEY_NAME)
        if not api_key or api_key != API_KEY:
            return Response(
                status_code=403,
                content={"detail": "Invalid API Key"},
                media_type="application/json"
            )
            
        return await call_next(request)


def add_security_middleware(app: FastAPI) -> None:
    """Add security middleware to a FastAPI app.
    
    Args:
        app: The FastAPI application
    """
    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Add rate limiting middleware
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        exclude_paths=["/health", "/docs", "/redoc", "/openapi.json"]
    )
    
    # Set up API key authentication
    setup_api_key_auth(app) 
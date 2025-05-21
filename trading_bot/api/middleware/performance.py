import time
import logging
import os
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables for performance settings
SLOW_REQUEST_THRESHOLD_MS = int(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500"))
VERY_SLOW_REQUEST_THRESHOLD_MS = int(os.getenv("VERY_SLOW_REQUEST_THRESHOLD_MS", "2000"))
ENABLE_PERFORMANCE_HEADERS = os.getenv("ENABLE_PERFORMANCE_HEADERS", "true").lower() == "true"

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance and log slow requests."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info(f"Performance monitoring initialized (slow threshold: {SLOW_REQUEST_THRESHOLD_MS}ms, very slow threshold: {VERY_SLOW_REQUEST_THRESHOLD_MS}ms)")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # Add request ID for tracking through logs
        request_id = f"{method}-{path}-{int(start_time * 1000) % 10000}"
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            process_time_ms = (time.time() - start_time) * 1000
            
            # Log based on response time
            if process_time_ms > VERY_SLOW_REQUEST_THRESHOLD_MS:
                logger.warning(f"VERY SLOW REQUEST [{request_id}]: {method} {path} took {process_time_ms:.2f}ms")
            elif process_time_ms > SLOW_REQUEST_THRESHOLD_MS:
                logger.info(f"SLOW REQUEST [{request_id}]: {method} {path} took {process_time_ms:.2f}ms")
            
            # Add performance headers if enabled
            if ENABLE_PERFORMANCE_HEADERS:
                response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
                response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate time even for errors
            process_time_ms = (time.time() - start_time) * 1000
            logger.error(f"REQUEST ERROR [{request_id}]: {method} {path} failed after {process_time_ms:.2f}ms - {str(e)}")
            raise

# Define helper functions to analyze performance in adhoc situations

def time_function(func):
    """Decorator to time function execution."""
    def wrapped(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(f"PERFORMANCE: {func.__name__} executed in {execution_time:.2f}ms")
        return result
    return wrapped

async def time_async_function(func):
    """Decorator to time async function execution."""
    async def wrapped(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        logger.info(f"PERFORMANCE: {func.__name__} executed in {execution_time:.2f}ms")
        return result
    return wrapped

def profile_block(name: str):
    """Context manager to profile a block of code.
    
    Usage:
        with profile_block("my operation"):
            # code to profile
    """
    class ProfileBlock:
        def __init__(self, name):
            self.name = name
            
        def __enter__(self):
            self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            execution_time = (time.time() - self.start_time) * 1000
            if exc_type:
                logger.info(f"PERFORMANCE [{self.name}]: failed after {execution_time:.2f}ms with {exc_type.__name__}")
            else:
                logger.info(f"PERFORMANCE [{self.name}]: completed in {execution_time:.2f}ms")
    
    return ProfileBlock(name) 
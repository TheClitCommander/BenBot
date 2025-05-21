import time
import logging
import functools
import os
from typing import Callable, Dict, List, Optional, Any, Union
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logger = logging.getLogger(__name__)

# Environment variables for monitoring settings
ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"
SLOW_REQUEST_THRESHOLD_MS = int(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500"))
ERROR_ALERT_THRESHOLD = int(os.getenv("ERROR_ALERT_THRESHOLD", "5"))

# In-memory metrics for basic monitoring
request_metrics = {
    "total_requests": 0,
    "error_count": 0,
    "endpoint_latency": {},  # Average latency by endpoint
    "recent_errors": [],     # List of recent errors for threshold alerting
    "status_codes": {}       # Count of responses by status code
}

# Flag to track if an alert has been sent
alert_sent = False


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor API requests, track metrics, and alert on issues."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # Reset the global metrics on restart
        global request_metrics
        request_metrics = {
            "total_requests": 0,
            "error_count": 0,
            "endpoint_latency": {},
            "recent_errors": [],
            "status_codes": {}
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        path = request.url.path
        
        # Track total requests
        global request_metrics
        request_metrics["total_requests"] += 1
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Record status code
            status_code = response.status_code
            request_metrics["status_codes"][str(status_code)] = request_metrics["status_codes"].get(str(status_code), 0) + 1
            
            # Calculate and store response time
            process_time_ms = (time.time() - start_time) * 1000
            
            # Track latency by endpoint
            if path not in request_metrics["endpoint_latency"]:
                request_metrics["endpoint_latency"][path] = {"count": 0, "total_ms": 0, "avg_ms": 0}
            
            endpoint_metrics = request_metrics["endpoint_latency"][path]
            endpoint_metrics["count"] += 1
            endpoint_metrics["total_ms"] += process_time_ms
            endpoint_metrics["avg_ms"] = endpoint_metrics["total_ms"] / endpoint_metrics["count"]
            
            # Log slow requests
            if process_time_ms > SLOW_REQUEST_THRESHOLD_MS:
                logger.warning(f"SLOW REQUEST: {request.method} {path} took {process_time_ms:.2f}ms to process")
            
            # Add performance header if enabled
            if ENABLE_PERFORMANCE_MONITORING:
                response.headers["X-Process-Time"] = f"{process_time_ms:.2f}ms"
            
            return response
            
        except Exception as e:
            # Track errors
            request_metrics["error_count"] += 1
            error_info = {
                "timestamp": time.time(),
                "path": path,
                "method": request.method,
                "error": str(e)
            }
            request_metrics["recent_errors"].append(error_info)
            
            # Keep only last 100 errors
            if len(request_metrics["recent_errors"]) > 100:
                request_metrics["recent_errors"] = request_metrics["recent_errors"][-100:]
            
            # Check if we need to alert on error rate
            check_error_threshold()
            
            # Re-raise the exception to let it be handled by exception handlers
            raise


def check_error_threshold():
    """Check if recent errors exceed threshold and trigger alert"""
    global alert_sent
    global request_metrics
    
    # Look at errors in the last minute
    now = time.time()
    one_minute_ago = now - 60
    
    recent_errors = [e for e in request_metrics["recent_errors"] if e["timestamp"] > one_minute_ago]
    
    if len(recent_errors) >= ERROR_ALERT_THRESHOLD and not alert_sent:
        alert_sent = True
        alert_message = f"ALERT: Error threshold exceeded with {len(recent_errors)} errors in the last minute"
        logger.error(alert_message)
        
        # Here you would typically integrate with an external alerting system
        # such as PagerDuty, Slack, email, etc.
        # For now, we'll just log the alert
        try:
            # Mock call to alert system
            send_alert(alert_message, recent_errors)
        except Exception as e:
            logger.error(f"Failed to send alert: {str(e)}")
    
    # Reset alert flag if no recent errors
    elif len(recent_errors) < ERROR_ALERT_THRESHOLD and alert_sent:
        alert_sent = False


def send_alert(message: str, errors: List[Dict[str, Any]]) -> None:
    """
    Send an alert to notification systems
    This is a placeholder function - in production, implement actual alert integrations
    """
    logger.error(f"{message}\nRecent errors: {errors}")
    # In a real system, you'd call your alerting service here


def get_metrics() -> Dict[str, Any]:
    """
    Get the current request metrics
    Used by the metrics endpoint to expose monitoring data
    """
    return request_metrics


def reset_metrics() -> None:
    """Reset all metrics - useful for testing"""
    global request_metrics
    request_metrics = {
        "total_requests": 0,
        "error_count": 0,
        "endpoint_latency": {},
        "recent_errors": [],
        "status_codes": {}
    }
    global alert_sent
    alert_sent = False 
"""
Error handling utilities for BensBot trading system.

This module provides error handling and resilience utilities including:
- Retry mechanism with exponential backoff
- Circuit breaker pattern implementation
- Error logging and monitoring
"""

import logging
import time
import functools
import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
import inspect
import random

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        exceptions_to_retry: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            backoff_factor: Multiplicative factor for delay after each retry
            max_delay: Maximum delay between retries in seconds
            jitter: Whether to add random jitter to delay
            exceptions_to_retry: List of exception types to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter
        self.exceptions_to_retry = exceptions_to_retry or [Exception]
    
    def should_retry(self, exception: Exception) -> bool:
        """
        Determine if retry should be attempted for this exception.
        
        Args:
            exception: The exception that was raised
            
        Returns:
            True if should retry, False otherwise
        """
        return any(isinstance(exception, exc_type) for exc_type in self.exceptions_to_retry)
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for a specific attempt.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay = delay - jitter_range + (random.random() * jitter_range * 2)
        
        return delay

def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    exceptions_to_retry: Optional[List[Type[Exception]]] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    on_failure: Optional[Callable[[Exception, int], Any]] = None
):
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplicative factor for delay after each retry
        max_delay: Maximum delay between retries in seconds
        jitter: Whether to add random jitter to delay
        exceptions_to_retry: List of exception types to retry on
        on_retry: Optional callback for retry attempts
        on_failure: Optional callback for final failure
        
    Returns:
        Decorated function
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        backoff_factor=backoff_factor,
        max_delay=max_delay,
        jitter=jitter,
        exceptions_to_retry=exceptions_to_retry
    )
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    
                    if not config.should_retry(e) or attempt >= config.max_attempts:
                        # Final failure - call failure callback if provided
                        if on_failure:
                            return on_failure(e, attempt)
                        # Otherwise re-raise
                        raise
                    
                    # Calculate delay
                    delay = config.get_delay(attempt)
                    
                    # Log retry
                    logger.warning(
                        f"Retry {attempt}/{config.max_attempts - 1} for {func.__name__} "
                        f"after error: {str(e)}. Waiting {delay:.2f}s before retry."
                    )
                    
                    # Call retry callback if provided
                    if on_retry:
                        on_retry(attempt, e, delay)
                    
                    # Wait before retry
                    time.sleep(delay)
        
        return wrapper
    
    return decorator

class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Call attempts fail immediately without executing the function
    - HALF_OPEN: A limited number of test calls are allowed to pass through
    """
    
    # Circuit states
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        test_calls: int = 1,
        exception_types: Optional[List[Type[Exception]]] = None
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of this circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before attempting recovery
            test_calls: Number of test calls allowed in half-open state
            exception_types: List of exception types to count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.test_calls = test_calls
        self.exception_types = exception_types or [Exception]
        
        # State
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.test_calls_remaining = 0
        
        self._lock = False  # Simple lock mechanism
    
    def __call__(self, func):
        """
        Decorator implementation.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._before_call()
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure(e)
                raise
        
        return wrapper
    
    def _before_call(self):
        """Check circuit state before making a call."""
        # Simple lock to avoid race conditions in state transitions
        while self._lock:
            time.sleep(0.01)
        
        self._lock = True
        try:
            # Check if circuit is open
            if self.state == self.OPEN:
                # Check if recovery timeout has elapsed
                if self.last_failure_time and \
                   datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                    # Transition to half-open
                    logger.info(f"Circuit {self.name} transitioning from OPEN to HALF-OPEN")
                    self.state = self.HALF_OPEN
                    self.test_calls_remaining = self.test_calls
                else:
                    # Circuit is still open
                    raise CircuitBreakerOpenError(
                        f"Circuit {self.name} is OPEN. "
                        f"Retry after {self._get_remaining_timeout()}s"
                    )
            
            # Check if in half-open state and no test calls remain
            if self.state == self.HALF_OPEN and self.test_calls_remaining <= 0:
                raise CircuitBreakerOpenError(
                    f"Circuit {self.name} is HALF-OPEN with no test calls remaining"
                )
            
            # Decrement test calls if in half-open state
            if self.state == self.HALF_OPEN:
                self.test_calls_remaining -= 1
        finally:
            self._lock = False
    
    def _on_success(self):
        """Handle successful call."""
        while self._lock:
            time.sleep(0.01)
        
        self._lock = True
        try:
            # If in half-open state and successful, close the circuit
            if self.state == self.HALF_OPEN:
                logger.info(f"Circuit {self.name} transitioning from HALF-OPEN to CLOSED after successful call")
                self.state = self.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
        finally:
            self._lock = False
    
    def _on_failure(self, exception: Exception):
        """Handle failed call."""
        # Check if this exception counts as a failure
        if not any(isinstance(exception, exc_type) for exc_type in self.exception_types):
            return
        
        while self._lock:
            time.sleep(0.01)
        
        self._lock = True
        try:
            # Record failure time
            self.last_failure_time = datetime.now()
            
            # If in half-open state, open the circuit again
            if self.state == self.HALF_OPEN:
                logger.warning(f"Circuit {self.name} transitioning from HALF-OPEN to OPEN after test call failure")
                self.state = self.OPEN
                return
            
            # If in closed state, increment failure counter
            if self.state == self.CLOSED:
                self.failure_count += 1
                
                # Check if threshold reached
                if self.failure_count >= self.failure_threshold:
                    logger.warning(
                        f"Circuit {self.name} transitioning from CLOSED to OPEN "
                        f"after {self.failure_count} failures"
                    )
                    self.state = self.OPEN
        finally:
            self._lock = False
    
    def _get_remaining_timeout(self) -> float:
        """Get remaining timeout in seconds."""
        if not self.last_failure_time:
            return 0
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - elapsed)
        return remaining
    
    def reset(self):
        """Reset the circuit breaker to closed state."""
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.test_calls_remaining = 0

class CircuitBreakerOpenError(Exception):
    """Exception raised when a circuit is open."""
    pass

class Fallback:
    """
    Decorator to provide fallback behavior for a function.
    
    This decorator allows specifying a fallback value or function
    to use when the decorated function raises an exception.
    """
    
    def __init__(
        self,
        fallback_value: Any = None,
        fallback_function: Optional[Callable] = None,
        exception_types: Optional[List[Type[Exception]]] = None,
        log_exceptions: bool = True
    ):
        """
        Initialize the fallback decorator.
        
        Args:
            fallback_value: Static value to return on failure
            fallback_function: Function to call on failure
            exception_types: List of exception types to catch
            log_exceptions: Whether to log the exception
        """
        self.fallback_value = fallback_value
        self.fallback_function = fallback_function
        self.exception_types = exception_types or [Exception]
        self.log_exceptions = log_exceptions
        
        if fallback_value is not None and fallback_function is not None:
            raise ValueError("Cannot specify both fallback_value and fallback_function")
    
    def __call__(self, func):
        """
        Decorator implementation.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if this exception should be caught
                if not any(isinstance(e, exc_type) for exc_type in self.exception_types):
                    raise
                
                # Log exception if requested
                if self.log_exceptions:
                    logger.warning(
                        f"Function {func.__name__} failed with {type(e).__name__}: {str(e)}. "
                        f"Using fallback."
                    )
                
                # Use fallback function if specified
                if self.fallback_function is not None:
                    if inspect.signature(self.fallback_function).parameters:
                        # If fallback function takes arguments, pass the exception
                        return self.fallback_function(e)
                    else:
                        # Otherwise call with no arguments
                        return self.fallback_function()
                
                # Otherwise return fallback value
                return self.fallback_value
        
        return wrapper

def rate_limit(
    calls: int,
    period: float,
    key_func: Optional[Callable] = None,
    on_limit: Optional[Callable[[], Any]] = None
):
    """
    Decorator to rate limit function calls.
    
    Args:
        calls: Number of calls allowed in the period
        period: Time period in seconds
        key_func: Optional function to extract a key from arguments
        on_limit: Optional function to call when limit is reached
        
    Returns:
        Decorated function
    """
    # Store call history
    call_history: Dict[str, List[float]] = {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine the rate limit key
            if key_func:
                key = str(key_func(*args, **kwargs))
            else:
                key = "default"
            
            # Get call times for this key
            times = call_history.setdefault(key, [])
            
            # Remove expired entries
            now = time.time()
            times = [t for t in times if now - t < period]
            
            # Check if limit reached
            if len(times) >= calls:
                if on_limit:
                    return on_limit()
                else:
                    oldest_call = min(times)
                    wait_time = period - (now - oldest_call)
                    raise RateLimitExceededError(
                        f"Rate limit of {calls} calls per {period}s exceeded. "
                        f"Try again in {wait_time:.2f}s"
                    )
            
            # Add current time and update history
            times.append(now)
            call_history[key] = times
            
            # Make the call
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

class RateLimitExceededError(Exception):
    """Exception raised when a rate limit is exceeded."""
    pass

def capture_exception(
    logger_instance: Optional[logging.Logger] = None,
    report_to_monitoring: bool = True,
    include_traceback: bool = True,
    additional_context: Optional[Dict[str, Any]] = None,
    severity: str = "error"
):
    """
    Decorator to capture and log exceptions.
    
    Args:
        logger_instance: Logger to use (defaults to module logger)
        report_to_monitoring: Whether to report to monitoring system
        include_traceback: Whether to include full traceback
        additional_context: Additional context data to include
        severity: Log level severity
        
    Returns:
        Decorated function
    """
    log = logger_instance or logger
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Build context
                context = {
                    "function": func.__name__,
                    "module": func.__module__,
                    "exception_type": type(e).__name__,
                    "exception_msg": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Add additional context if provided
                if additional_context:
                    context.update(additional_context)
                
                # Add traceback if requested
                if include_traceback:
                    context["traceback"] = traceback.format_exc()
                
                # Log the exception with context
                log_msg = f"Exception in {func.__name__}: {str(e)}"
                
                if severity == "critical":
                    log.critical(log_msg, extra={"context": context})
                elif severity == "error":
                    log.error(log_msg, extra={"context": context})
                elif severity == "warning":
                    log.warning(log_msg, extra={"context": context})
                else:
                    log.error(log_msg, extra={"context": context})
                
                # Report to monitoring system if requested
                if report_to_monitoring:
                    try:
                        _report_to_monitoring(e, context)
                    except Exception as monitoring_error:
                        log.warning(f"Failed to report to monitoring: {monitoring_error}")
                
                # Re-raise the original exception
                raise
        
        return wrapper
    
    return decorator

def _report_to_monitoring(exception: Exception, context: Dict[str, Any]):
    """
    Report exception to monitoring system.
    
    This is a placeholder function. In a real system, this would send data
    to Prometheus, Sentry, New Relic, etc.
    
    Args:
        exception: The exception that occurred
        context: Context data about the exception
    """
    # This would be implemented with actual monitoring integrations
    # For example, Sentry, Prometheus, New Relic, etc.
    pass 
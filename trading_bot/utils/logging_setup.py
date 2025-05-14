"""
Logging Setup for BensBot.

This module provides consistent logging configuration across the application.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: str = DEFAULT_LOG_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    component_levels: Optional[Dict[str, str]] = None
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Default logging level for all loggers
        log_file: Optional file path to write logs to
        log_format: Format string for log messages
        date_format: Format string for timestamps
        component_levels: Dict mapping logger names to specific levels
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to prevent duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(log_format, date_format)
    
    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure file handler if specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific levels for components if provided
    if component_levels:
        for logger_name, level in component_levels.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Log startup message
    root_logger.info(f"Logging initialized at {datetime.now().isoformat()} - Level: {log_level}")

def get_component_logger(component_name: str) -> logging.Logger:
    """
    Get a logger configured for a specific component.
    
    Args:
        component_name: Name of the component (e.g., 'trading_bot.core.evolution')
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(component_name)
    
    # If no handlers exist, logging may not be initialized yet
    if not logger.handlers and not logger.parent.handlers:
        setup_logging()
        logger.debug(f"Auto-initialized logging for {component_name}")
    
    return logger

def log_method_call(logger: logging.Logger, level: int = logging.DEBUG):
    """
    Decorator to log method entry and exit.
    
    Args:
        logger: Logger to use
        level: Logging level for the messages
    
    Example:
        @log_method_call(logger)
        def some_method(self, arg1, arg2):
            # Method implementation
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            class_name = ""
            if args and hasattr(args[0], "__class__"):
                class_name = args[0].__class__.__name__ + "."
            
            logger.log(level, f"Entering {class_name}{func_name}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"Exiting {class_name}{func_name}")
                return result
            except Exception as e:
                logger.exception(f"Exception in {class_name}{func_name}: {e}")
                raise
        return wrapper
    return decorator 
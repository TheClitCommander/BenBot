"""
Logging configuration for BensBot trading system.

This module provides a structured logging setup with features including:
- Log rotation
- Different log levels per module
- Structured JSON logging for machine processing
- Console and file handlers
- Custom formatters for different outputs
"""

import os
import sys
import json
import logging
import logging.config
import logging.handlers
import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
import traceback
import socket

# Default log format for console output
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# More detailed format for file logs
DETAILED_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(module)s:%(lineno)d] - %(message)s"

# JSON format for structured logging
class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    
    This formatter is used for structured logging that can be easily 
    processed by log aggregation tools.
    """
    
    def __init__(
        self,
        fmt_dict: Optional[Dict[str, Any]] = None,
        time_format: str = "%Y-%m-%d %H:%M:%S.%f"
    ):
        """
        Initialize the formatter with a format dictionary.
        
        Args:
            fmt_dict: Dictionary of log format fields
            time_format: Time format string
        """
        super().__init__()
        self.fmt_dict = fmt_dict or {
            "timestamp": "asctime",
            "level": "levelname",
            "name": "name",
            "module": "module",
            "function": "funcName",
            "line": "lineno",
            "thread_id": "thread",
            "process_id": "process",
            "message": "message"
        }
        self.default_time_format = time_format
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON string
        """
        record_dict = {}
        
        # Apply standard formatting
        record.asctime = self.formatTime(record, self.default_time_format)
        record.message = record.getMessage()
        
        # Add configured fields
        for key, field_name in self.fmt_dict.items():
            if hasattr(record, field_name):
                value = getattr(record, field_name)
                record_dict[key] = value
        
        # Add exception info if available
        if record.exc_info:
            record_dict["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[2] else None
            }
        
        # Add extra attributes
        if hasattr(record, "props"):
            record_dict["props"] = record.props
        
        # Add hostname
        record_dict["hostname"] = socket.gethostname()
        
        # Add record attributes not in the format dict but in record.__dict__
        for key, value in record.__dict__.items():
            if key not in self.fmt_dict.values() and key not in ["args", "msg", "exc_info", "exc_text", "stack_info"] and key.startswith("_"):
                try:
                    record_dict[key] = value
                except (TypeError, ValueError):
                    # Skip values that can't be serialized
                    record_dict[key] = str(value)
        
        # Convert to JSON
        try:
            return json.dumps(record_dict)
        except (TypeError, ValueError) as e:
            # Fallback in case of serialization errors
            simplified_record = {
                "timestamp": record.asctime,
                "level": record.levelname,
                "name": record.name,
                "message": record.message,
                "serialization_error": str(e)
            }
            return json.dumps(simplified_record)

def setup_logging(
    log_dir: str = "./logs",
    log_level: Union[str, int] = logging.INFO,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = True,
    log_filename: str = "bensbot.log",
    json_filename: str = "bensbot.json.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 10,
    module_levels: Optional[Dict[str, Union[str, int]]] = None
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_dir: Directory to store log files
        log_level: Default log level
        enable_console: Whether to enable console logging
        enable_file: Whether to enable file logging
        enable_json: Whether to enable JSON structured logging
        log_filename: Filename for regular log file
        json_filename: Filename for JSON structured log file
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        module_levels: Dictionary of module names -> log levels
    """
    # Convert log level string to int if needed
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create log directory if it doesn't exist
    log_dir_path = Path(log_dir)
    os.makedirs(log_dir_path, exist_ok=True)
    
    # Prepare handlers configuration
    handlers = {}
    
    # Console handler
    if enable_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level,
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        }
    
    # File handler
    if enable_file:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "detailed",
            "filename": os.path.join(log_dir, log_filename),
            "maxBytes": max_file_size,
            "backupCount": backup_count,
            "encoding": "utf8"
        }
    
    # JSON handler
    if enable_json:
        handlers["json_file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": log_level,
            "formatter": "json",
            "filename": os.path.join(log_dir, json_filename),
            "maxBytes": max_file_size,
            "backupCount": backup_count,
            "encoding": "utf8"
        }
    
    # Prepare loggers configuration
    loggers = {
        "": {  # Root logger
            "level": log_level,
            "handlers": list(handlers.keys()),
            "propagate": False
        }
    }
    
    # Add module-specific log levels
    if module_levels:
        for module_name, level in module_levels.items():
            if isinstance(level, str):
                level = getattr(logging, level.upper(), logging.INFO)
            
            loggers[module_name] = {
                "level": level,
                "handlers": list(handlers.keys()),
                "propagate": False
            }
    
    # Build final config
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": DEFAULT_LOG_FORMAT
            },
            "detailed": {
                "format": DETAILED_LOG_FORMAT
            },
            "json": {
                "()": JsonFormatter
            }
        },
        "handlers": handlers,
        "loggers": loggers
    }
    
    # Apply configuration
    logging.config.dictConfig(log_config)
    
    # Log startup message
    root_logger = logging.getLogger()
    root_logger.info(
        "Logging initialized at %s - Level: %s",
        datetime.datetime.now().isoformat(),
        logging.getLevelName(log_level)
    )

def get_component_logger(
    component_name: str,
    level: Optional[Union[str, int]] = None
) -> logging.Logger:
    """
    Get a logger for a specific component with optional level override.
    
    Args:
        component_name: Name of the component (typically the module name)
        level: Optional log level override
        
    Returns:
        Logger instance for the component
    """
    logger = logging.getLogger(component_name)
    
    if level is not None:
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(level)
    
    return logger

def log_with_context(
    logger: logging.Logger,
    level: int,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    exc_info: Optional[Any] = None,
    stack_info: bool = False,
    stacklevel: int = 1,
    **kwargs
) -> None:
    """
    Log a message with added context information.
    
    Args:
        logger: Logger to use
        level: Log level
        msg: Log message
        context: Additional context data
        exc_info: Exception information
        stack_info: Whether to include stack info
        stacklevel: Stack frame level
        **kwargs: Additional logging parameters
    """
    # Create a log record with context
    if context:
        extra = kwargs.get("extra", {})
        # Store context in props for the JSON formatter
        extra["props"] = context
        kwargs["extra"] = extra
    
    # Use the logger's _log method directly
    logger._log(
        level,
        msg,
        args=kwargs.get("args", ()),
        exc_info=exc_info,
        stack_info=stack_info,
        stacklevel=stacklevel,
        extra=kwargs.get("extra", None)
    )

# Utility functions for common log levels

def debug_with_context(
    logger: logging.Logger,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log a debug message with context.
    
    Args:
        logger: Logger to use
        msg: Log message
        context: Additional context data
        **kwargs: Additional logging parameters
    """
    log_with_context(logger, logging.DEBUG, msg, context, **kwargs)

def info_with_context(
    logger: logging.Logger,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log an info message with context.
    
    Args:
        logger: Logger to use
        msg: Log message
        context: Additional context data
        **kwargs: Additional logging parameters
    """
    log_with_context(logger, logging.INFO, msg, context, **kwargs)

def warning_with_context(
    logger: logging.Logger,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log a warning message with context.
    
    Args:
        logger: Logger to use
        msg: Log message
        context: Additional context data
        **kwargs: Additional logging parameters
    """
    log_with_context(logger, logging.WARNING, msg, context, **kwargs)

def error_with_context(
    logger: logging.Logger,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log an error message with context.
    
    Args:
        logger: Logger to use
        msg: Log message
        context: Additional context data
        **kwargs: Additional logging parameters
    """
    log_with_context(logger, logging.ERROR, msg, context, **kwargs)

def critical_with_context(
    logger: logging.Logger,
    msg: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log a critical message with context.
    
    Args:
        logger: Logger to use
        msg: Log message
        context: Additional context data
        **kwargs: Additional logging parameters
    """
    log_with_context(logger, logging.CRITICAL, msg, context, **kwargs) 
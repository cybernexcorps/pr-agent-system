"""
Structured logging configuration for PR Agent.

Uses structlog to provide structured, JSON-formatted logging with context.
"""

import logging
import sys
from typing import Any, Dict, Optional
import structlog
from structlog.types import EventDict, WrappedLogger


def add_log_level(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add log level to event dict."""
    if method_name == "warn":
        method_name = "warning"
    event_dict["level"] = method_name.upper()
    return event_dict


def add_timestamp(
    logger: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add ISO timestamp to event dict."""
    import datetime
    event_dict["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_verbose: bool = True
) -> None:
    """
    Configure structured logging for the PR Agent.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - "json" for structured JSON or "console" for human-readable
        enable_verbose: Whether to enable verbose logging
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=numeric_level,
    )

    # Determine processors based on format
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level,
        add_timestamp,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("processing_request", executive="John Doe", step="load_profile")
    """
    return structlog.get_logger(name)


class LogContext:
    """
    Context manager for adding structured context to logs.

    Example:
        >>> with LogContext(executive="John Doe", media_outlet="TechCrunch"):
        ...     logger.info("processing_comment")
        # Log will include executive and media_outlet fields
    """

    def __init__(self, **context: Any):
        """
        Initialize log context.

        Args:
            **context: Key-value pairs to add to all logs in this context
        """
        self.context = context
        self.token: Optional[Any] = None

    def __enter__(self) -> "LogContext":
        """Enter context - bind context to logger."""
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context - unbind context from logger."""
        if self.token is not None:
            structlog.contextvars.unbind_contextvars(*self.context.keys())


def log_execution_time(func):
    """
    Decorator to log execution time of functions.

    Usage:
        @log_execution_time
        async def my_function():
            ...
    """
    import functools
    import time
    import asyncio

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                "function_completed",
                function=func.__name__,
                duration_seconds=round(duration, 3),
                success=True
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "function_failed",
                function=func.__name__,
                duration_seconds=round(duration, 3),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                "function_completed",
                function=func.__name__,
                duration_seconds=round(duration, 3),
                success=True
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                "function_failed",
                function=func.__name__,
                duration_seconds=round(duration, 3),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper

"""Structured logging with OpenTelemetry integration.

This module provides logging utilities that automatically inject trace context
when OpenTelemetry is enabled, making it easier to correlate logs with traces.
"""

import logging
from typing import Any

from litestar.connection import Request
from opentelemetry import trace

from app.config import settings


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with optional OpenTelemetry trace context.

    Args:
        name: The logger name (typically __name__ from the calling module)

    Returns:
        A configured logger instance

    Example:
        ```python
        from app.logging import get_logger

        logger = get_logger(__name__)
        logger.info("Processing signup", extra={"signup_id": signup.id})
        ```
    """
    logger = logging.getLogger(name)

    # Set log level from configuration
    if settings.otel_enabled:
        logger.setLevel(getattr(logging, settings.otel_log_level.upper(), logging.INFO))

    return logger


def log_with_trace(logger: logging.Logger, level: int, msg: str, **kwargs: Any) -> None:
    """Log a message with OpenTelemetry trace context if available.

    This function automatically adds trace_id and span_id to log records when
    OpenTelemetry tracing is active, making it easier to correlate logs with traces.

    Args:
        logger: The logger instance to use
        level: The log level (e.g., logging.INFO, logging.ERROR)
        msg: The log message
        **kwargs: Additional key-value pairs to include in the log record

    Example:
        ```python
        from app.logging import get_logger, log_with_trace
        import logging

        logger = get_logger(__name__)
        log_with_trace(logger, logging.INFO, "User logged in", user_id=user.id)
        ```
    """
    extra = kwargs.copy()

    # Add trace context if available
    if settings.otel_enabled:
        span = trace.get_current_span()
        if span and span.is_recording():
            span_context = span.get_span_context()
            extra["trace_id"] = format(span_context.trace_id, "032x")
            extra["span_id"] = format(span_context.span_id, "016x")

    logger.log(level, msg, extra=extra)


def log_request_event(
    logger: logging.Logger,
    level: int,
    msg: str,
    request: Request | None = None,
    **kwargs: Any,
) -> None:
    """Log with request context automatically included.

    Enhances logging with HTTP request details like method, path, client IP, etc.

    Args:
        logger: The logger instance to use
        level: The log level
        msg: The log message
        request: Optional Litestar Request object
        **kwargs: Additional key-value pairs to include in the log record

    Example:
        ```python
        from app.logging import get_logger, log_request_event
        import logging

        @get("/")
        async def handler(request: Request):
            logger = get_logger(__name__)
            log_request_event(
                logger, logging.INFO, "Processing request",
                request=request,
                user_id=user_id
            )
        ```
    """
    extra = kwargs.copy()

    # Add request context if available
    if request:
        extra.update(
            {
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_type": request.headers.get("content-type"),
            }
        )

    log_with_trace(logger, level, msg, **extra)

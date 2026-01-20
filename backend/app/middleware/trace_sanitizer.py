"""Middleware for sanitizing sensitive data from OpenTelemetry traces.

This module provides utilities to redact sensitive data such as authorization tokens,
passwords, and API keys from span attributes and log records before export.

Note: OpenTelemetry span attributes are immutable, so this module focuses on:
1. Logging sensitive data redaction (modifiable dicts)
2. Guidance for creating spans without sensitive data
3. HTTP header/body filtering at middleware level
"""

from typing import Any

# Headers that should not appear in traces
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-auth-token",
    "x-csrf-token",
    "x-token",
    "api-key",
    "password",
    "secret",
}

# Query parameters that should be redacted
SENSITIVE_QUERY_PARAMS = {
    "token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "auth",
    "access_token",
    "refresh_token",
    "session_id",
}

# Body field patterns that should be redacted
SENSITIVE_BODY_FIELDS = {
    "password",
    "secret",
    "api_key",
    "token",
    "authorization",
    "credit_card",
    "ssn",
    "email",  # PII
    "phone",  # PII
}


def is_sensitive_header(header_name: str) -> bool:
    """Check if a header name is sensitive.

    Args:
        header_name: The HTTP header name

    Returns:
        True if the header contains sensitive data
    """
    header_lower = header_name.lower()
    return any(sensitive in header_lower for sensitive in SENSITIVE_HEADERS)


def is_sensitive_query_param(param_name: str) -> bool:
    """Check if a query parameter name is sensitive.

    Args:
        param_name: The query parameter name

    Returns:
        True if the parameter contains sensitive data
    """
    param_lower = param_name.lower()
    return any(sensitive in param_lower for sensitive in SENSITIVE_QUERY_PARAMS)


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name is sensitive.

    Args:
        field_name: The field name

    Returns:
        True if the field contains sensitive data
    """
    field_lower = field_name.lower()
    return any(sensitive in field_lower for sensitive in SENSITIVE_BODY_FIELDS)


def redact_url(url: str) -> str:
    """Redact sensitive query parameters from URL.

    Args:
        url: The URL to redact

    Returns:
        The URL with sensitive query parameters redacted
    """
    if "?" not in url:
        return url

    base, query = url.split("?", 1)
    params = query.split("&")

    redacted_params = []
    for param in params:
        if "=" in param:
            key, value = param.split("=", 1)
            if is_sensitive_query_param(key):
                redacted_params.append(f"{key}=[REDACTED]")
            else:
                redacted_params.append(param)
        else:
            redacted_params.append(param)

    return f"{base}?{'&'.join(redacted_params)}"


def sanitize_log_attributes(record: dict[str, Any]) -> dict[str, Any]:
    """Sanitize sensitive data from log records.

    Args:
        record: The log record attributes

    Returns:
        The sanitized log record
    """
    sanitized = record.copy()

    for key in list(sanitized.keys()):
        # Skip span/trace context fields
        if key in ("trace_id", "span_id", "timestamp", "level", "message"):
            continue

        # Check for sensitive patterns
        if is_sensitive_header(key) or is_sensitive_query_param(key) or is_sensitive_field(key):
            sanitized[key] = "[REDACTED]"
        elif key == "url" and isinstance(sanitized[key], str):
            sanitized[key] = redact_url(sanitized[key])

    return sanitized

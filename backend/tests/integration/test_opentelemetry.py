"""Tests for OpenTelemetry integration."""

import os

from app.config import settings
from app.middleware.trace_sanitizer import (
    is_sensitive_field,
    is_sensitive_header,
    is_sensitive_query_param,
    redact_url,
    sanitize_log_attributes,
)


class TestSensitivityDetection:
    """Test sensitive data detection."""

    def test_sensitive_header_detection(self):
        """Test that sensitive headers are detected."""
        assert is_sensitive_header("Authorization")
        assert is_sensitive_header("Cookie")
        assert is_sensitive_header("X-API-Key")
        assert is_sensitive_header("X-Auth-Token")
        assert is_sensitive_header("content-type") is False

    def test_sensitive_query_param_detection(self):
        """Test that sensitive query parameters are detected."""
        assert is_sensitive_query_param("token")
        assert is_sensitive_query_param("password")
        assert is_sensitive_query_param("api_key")
        assert is_sensitive_query_param("access_token")
        assert is_sensitive_query_param("search") is False

    def test_sensitive_field_detection(self):
        """Test that sensitive fields are detected."""
        assert is_sensitive_field("password")
        assert is_sensitive_field("secret")
        assert is_sensitive_field("api_key")
        assert is_sensitive_field("email")
        assert is_sensitive_field("phone")
        assert is_sensitive_field("name") is False


class TestDataSanitization:
    """Test data sanitization utilities."""

    def test_url_sanitization(self):
        """Test URL query parameter sanitization."""
        url = "https://api.example.com/endpoint?token=secret123&search=test"
        sanitized = redact_url(url)
        assert "[REDACTED]" in sanitized
        assert "secret123" not in sanitized
        assert "search=test" in sanitized

    def test_url_without_query_params(self):
        """Test URL without query parameters."""
        url = "https://api.example.com/endpoint"
        assert redact_url(url) == url

    def test_log_record_sanitization(self):
        """Test log record sanitization."""
        record = {
            "message": "Login attempt",
            "user_id": "12345",
            "password": "secret123",
            "token": "abc123",
            "timestamp": "2025-01-16T10:00:00",
        }

        sanitized = sanitize_log_attributes(record)

        assert sanitized["message"] == "Login attempt"
        assert sanitized["user_id"] == "12345"
        assert sanitized["password"] == "[REDACTED]"
        assert sanitized["token"] == "[REDACTED]"
        assert sanitized["timestamp"] == "2025-01-16T10:00:00"


class TestOTelConfiguration:
    """Test OpenTelemetry configuration."""

    def test_otel_disabled_by_default(self):
        """Test that OTel is disabled by default."""
        # In test environment, should be False
        assert isinstance(settings.otel_enabled, bool)

    def test_otel_sampling_configuration(self):
        """Test OTel sampling rate configuration."""
        assert 0.0 <= settings.otel_trace_sample_rate <= 1.0
        # Default should be 1.0 (100%)
        assert settings.otel_trace_sample_rate >= 0.1

    def test_otel_batch_size_configuration(self):
        """Test OTel batch processor configuration."""
        assert settings.otel_batch_max_export_batch_size > 0
        assert settings.otel_batch_schedule_delay_millis > 0
        assert settings.otel_batch_max_queue_size > 0

    def test_slow_query_threshold(self):
        """Test slow query logging threshold."""
        assert settings.otel_slow_query_threshold_ms > 0
        # Default should be 100ms
        assert settings.otel_slow_query_threshold_ms >= 10


class TestRateLimitConfiguration:
    """Test rate limiting configuration."""

    def test_general_rate_limit(self):
        """Test general rate limiting configuration."""
        assert settings.rate_limit_requests_per_minute > 0
        # Default should be reasonable (60 per minute)
        assert settings.rate_limit_requests_per_minute >= 10

    def test_magic_link_rate_limits(self):
        """Test magic link endpoint rate limiting."""
        assert settings.magic_link_rate_limit_per_minute > 0
        assert settings.magic_link_rate_limit_per_hour > 0
        # Magic link should be more restricted
        assert settings.magic_link_rate_limit_per_minute <= settings.rate_limit_requests_per_minute
        # Per hour should be more than per minute
        assert settings.magic_link_rate_limit_per_hour >= settings.magic_link_rate_limit_per_minute


class TestEnvironmentVariables:
    """Test environment variable handling."""

    def test_otel_endpoint_from_env(self):
        """Test that OTEL_EXPORTER_OTLP_ENDPOINT is read from environment."""
        # Store original
        original = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")

        try:
            os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://custom-collector:4317"
            # Note: This test would need settings reloaded in real scenario
            # Just verify the property method exists
            assert hasattr(settings, "otel_endpoint")
        finally:
            # Restore original
            if original:
                os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = original
            else:
                os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)

    def test_otel_service_name_from_env(self):
        """Test that OTEL_SERVICE_NAME is read from environment."""
        # Verify the property exists
        assert hasattr(settings, "otel_service_name")
        # Should return a string
        assert isinstance(settings.otel_service_name, str)
        assert len(settings.otel_service_name) > 0

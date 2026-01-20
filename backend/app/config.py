from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sessions"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Application
    debug: bool = False

    # SQLAlchemy
    # Controls whether SQL statements are echoed to logs.
    # Keep this separate from `debug` to avoid noisy logs in dev/compose.
    sqlalchemy_echo: bool = False
    cors_origins: str = "http://localhost:4321,http://localhost:4324,http://localhost:3001,http://localhost:8000,http://localhost:4173,https://sessions.tuhuratech.org.nz,https://sessions-admin.tuhuratech.org.nz"
    public_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:4324"
    admin_base_url: str = "http://localhost:3001"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    # Auth (caregiver magic link)
    auth_secret: str = "dev-secret-change-me"
    magic_link_ttl_minutes: int = 15
    caregiver_session_ttl_days: int = 30

    # Admin auth (OAuth + server-issued session)
    admin_session_ttl_hours: int = 24
    # Admin OAuth (Google)
    admin_google_oauth_client_id: str = ""
    admin_google_oauth_client_secret: str = ""

    # Email
    email_from: str = ""
    email_from_name: str = ""
    email_contact: str = ""
    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mailgun_api_url: str = ""
    email_dry_run: bool = False  # Don't actually send emails in dev/test

    # Newsletter
    newsletter_webhook_url: str = ""
    newsletter_webhook_token: str = ""

    # OpenTelemetry / Observability
    otel_enabled: bool = False
    otel_log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    otel_trace_sample_rate: float = 1.0  # 1.0 = 100%, 0.1 = 10%
    otel_batch_max_export_batch_size: int = 256
    otel_batch_schedule_delay_millis: int = 5000  # 5 seconds
    otel_batch_max_queue_size: int = 2048
    otel_slow_query_threshold_ms: float = 100.0  # Log queries slower than this

    # Rate limiting
    rate_limit_requests_per_minute: int = 60  # General rate limit
    magic_link_rate_limit_per_minute: int = 3  # Strict limit on magic link endpoint
    magic_link_rate_limit_per_hour: int = 10  # Max 10 magic link requests per hour per email

    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def otel_endpoint(self) -> str:
        """Get OTLP endpoint from environment or return default."""
        import os

        return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    @property
    def otel_protocol(self) -> str:
        """Get OTLP protocol from environment or return default."""
        import os

        return os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc")

    @property
    def otel_service_name(self) -> str:
        """Get service name from environment or return default."""
        import os

        return os.getenv("OTEL_SERVICE_NAME", "tuhura-sessions-api")


settings = Settings()

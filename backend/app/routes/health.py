"""Health check endpoint."""

from datetime import UTC, datetime

from litestar import Controller, get

from app.config import settings


class HealthController(Controller):
    """Health check endpoints."""

    path = ""
    tags = ["Health"]

    @get("/api/v1/health", summary="Health check")
    async def health_check(self) -> dict:
        """Health check endpoint with telemetry and version information.

        Returns:
            Health status including service version and telemetry info
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "version": "1.0.0",
            "service": "tuhura-sessions-api",
            "debug": settings.debug,
        }

    @get("/api/v1/health/ready", summary="Readiness check")
    async def readiness_check(self) -> dict:
        """Readiness check for Kubernetes/orchestrators.

        Returns:
            Readiness status
        """
        # In the future, add database connectivity checks, cache checks, etc.
        return {
            "ready": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @get("/api/v1/health/live", summary="Liveness check")
    async def liveness_check(self) -> dict:
        """Liveness check for Kubernetes/orchestrators.

        Returns:
            Liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }

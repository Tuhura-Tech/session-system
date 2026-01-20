import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from litestar import Litestar, Request, Response
from litestar.config.cors import CORSConfig
from litestar.contrib.opentelemetry import OpenTelemetryConfig
from litestar.exceptions import NotAuthorizedException
from litestar.middleware.base import DefineMiddleware
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.spec import Tag
from litestar.plugins.pydantic import PydanticPlugin
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from app.config import settings
from app.db import lifespan_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.routes.admin import AdminController
from app.routes.admin_auth import AdminAuthController
from app.routes.auth import AuthController
from app.routes.caregiver import CaregiverController
from app.routes.health import HealthController
from app.routes.public import PublicController
from app.routes.staff_admin import SessionStaffController, StaffAdminController

# Reduce SQLAlchemy log noise (query + schema inspection logs).
# If SQL echo is explicitly enabled, don't interfere.
if not settings.sqlalchemy_echo:
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

logger.info("Application starting up. Debug=%s", settings.debug)


def auth_exception_handler(request: Request, exc: NotAuthorizedException) -> Response:
    """Handle authentication exceptions without logging a full traceback."""
    # Log at INFO level without traceback since this is expected behavior
    logger.info(f"Authentication failed: {exc.detail} - {request.method} {request.url.path}")

    return Response(
        content={"detail": exc.detail},
        status_code=HTTP_401_UNAUTHORIZED,
        headers={"WWW-Authenticate": "Bearer"},
    )


@asynccontextmanager
async def lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    async with lifespan_db():
        yield


cors_config = CORSConfig(
    allow_origins=settings.cors_origins,
    allow_headers=["*"],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_credentials=True,
)

openapi_config = OpenAPIConfig(
    title="Tūhura Tech Sessions API",
    version="1.0.0",
    description=(
        "Backend API for the Tūhura Tech Sessions site.\n\n"
        "API v1\n\n"
        "Groups:\n"
        "- Public: session discovery + session details (no auth)\n"
        "- Auth: caregiver magic-link sign-in/out\n"
        "- Caregiver: authenticated caregiver profile/children/signups\n"
        "- Admin Auth: Google OAuth for admin UI\n"
        "- Admin: staff/admin management endpoints"
    ),
    render_plugins=[ScalarRenderPlugin()],
    path="/docs",
    use_handler_docstrings=True,
    tags=[
        Tag(
            name="Public",
            description="Unauthenticated endpoints used by the public site.",
        ),
        Tag(name="Caregiver", description="Authenticated caregiver endpoints."),
        Tag(name="Auth", description="Caregiver authentication via magic links."),
        Tag(name="Admin Auth", description="Admin authentication via Google OAuth."),
        Tag(
            name="Admin: Terms",
            description="Manage school terms used for term schedules.",
        ),
        Tag(
            name="Admin: Exclusions",
            description="Manage exclusion dates (holidays, closures).",
        ),
        Tag(
            name="Admin: Locations",
            description="Manage session locations and contact details.",
        ),
        Tag(
            name="Admin: Sessions",
            description="Manage sessions (schedule, capacity, waitlist).",
        ),
        Tag(
            name="Admin: Occurrences",
            description="Manage and generate session occurrences.",
        ),
        Tag(name="Admin: Signups", description="View and update caregiver signups."),
        Tag(
            name="Admin: Attendance",
            description="Roll + attendance recording and audit.",
        ),
        Tag(name="Admin: Children", description="Child details and internal notes."),
        Tag(
            name="Admin: Communications",
            description="Bulk email and change notifications.",
        ),
        Tag(name="Admin: Exports", description="CSV exports for signups and attendance."),
        Tag(
            name="Admin - Staff",
            description="Manage staff members and session assignments.",
        ),
    ],
)

# Configure OpenTelemetry if enabled
# Note: OpenTelemetry service name and other settings should be configured via
# environment variables like OTEL_SERVICE_NAME, OTEL_EXPORTER_OTLP_ENDPOINT
otel_config = None
if settings.otel_enabled:
    otel_config = OpenTelemetryConfig()

app = Litestar(
    route_handlers=[
        PublicController,
        AuthController,
        CaregiverController,
        AdminAuthController,
        AdminController,
        StaffAdminController,
        SessionStaffController,
        HealthController,
    ],
    lifespan=[lifespan],
    cors_config=cors_config,
    openapi_config=openapi_config,
    plugins=[PydanticPlugin(prefer_alias=True)],
    middleware=[DefineMiddleware(RateLimitMiddleware)] + ([otel_config.middleware] if otel_config else []),
    exception_handlers={NotAuthorizedException: auth_exception_handler},
    debug=settings.debug,
)

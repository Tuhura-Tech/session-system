from __future__ import annotations

# from typing import TYPE_CHECKING, TypeVar

# from litestar.di import Provide
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.plugins import CLIPluginProtocol, InitPluginProtocol

from app.db import models as m

# from litestar.security.jwt import OAuth2Login

# if TYPE_CHECKING:
#     from litestar.config.app import AppConfig


# T = TypeVar("T")


class ApplicationCore(InitPluginProtocol, CLIPluginProtocol):
    """Application core configuration plugin.

    This class is responsible for configuring the main Litestar application with our routes, guards, and various plugins

    """

    # __slots__ = ("app_slug",)
    # app_slug: str

    def on_app_init(self, app_config):
        """Configure application for use with SQLAlchemy.

        Args:
            app_config: The :class:`AppConfig <litestar.config.app.AppConfig>` instance.

        Returns:
            The configured app config.
        """
        # from datetime import datetime
        # from uuid import UUID

        # from advanced_alchemy.exceptions import DuplicateKeyError, RepositoryError
        # from httpx_oauth.oauth2 import OAuth2Token
        # from litestar.enums import RequestEncodingType
        # from litestar.params import Body
        # from litestar.security.jwt import Token

        # from app import config
        # from app.db import models as m
        # from app.domain.accounts.guards import auth, provide_user
        # from app.lib.exceptions import (
        #     ApplicationClientError,
        #     ApplicationError,
        #     exception_to_http_response,
        # )
        # from app.lib.settings import AppSettings, get_settings, provide_app_settings
        # from app.domain.admin.guards import admin_session_guard
        from app.lib.settings import settings

        # from app.lib.validation import ValidationError
        from app.server import plugins
        from app.domains.public.controllers.health import HealthController
        from app.domains.public.controllers.sessions import SessionController
        from app.domains.caregiver.controllers.caregiver import CaregiverController
        from app.domains.admin.controllers import (
            LocationController,
            StaffController,
            ExclusionController,
            BlockController,
            StudentController,
            SignupController,
            OccurrenceController,
            SessionController as AdminSessionController,
        )

        # settings = get_settings()
        # app_config.debug = settings.debug
        app_config.openapi_config = OpenAPIConfig(
            title="Tūhura Tech Sessions API",
            version="latest",
            path="/docs",
            description=("Backend API for the Tūhura Tech Sessions site.\n\n"),
            # components=[auth.openapi_components],
            # security=[auth.security_requirement],
            render_plugins=[ScalarRenderPlugin(version="latest")],
        )

        app_config.plugins.extend(
            [
                plugins.granian,
                plugins.alchemy,
                plugins.get_saq_plugin(),
                plugins.oauth2_provider,
                # plugins.domain,
            ],
        )

        app_config.signature_namespace.update(
            {
                # "Token": Token,
                # "OAuth2Login": OAuth2Login,
                # "RequestEncodingType": RequestEncodingType,
                # "Body": Body,
                "m": m,
                # "UUID": UUID,
                # "datetime": datetime,
                # "OAuth2Token": OAuth2Token,
                # "AppSettings": AppSettings,
                # "Caregiver": m.Caregiver,
                # "AppEmailService": AppEmailService,
                # "EmailService": EmailService,
            },
        )

        app_config.route_handlers = [
            HealthController,
            SessionController,
            CaregiverController,
            LocationController,
            AdminSessionController,
            StaffController,
            ExclusionController,
            BlockController,
            StudentController,
            SignupController,
            OccurrenceController,
        ]

        app_config.debug = True

        return app_config

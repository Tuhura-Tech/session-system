from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def setup_environment() -> None:
    """Configure the environment variables and path."""
    current_path = Path(__file__).parent.parent.resolve()
    sys.path.append(str(current_path))
    # from litestar.cli._utils import LitestarExtensionGroup

    from app.lib.settings import settings

    os.environ.setdefault("LITESTAR_APP", "app.server.asgi:create_app")
    os.environ.setdefault("LITESTAR_APP_NAME", settings.app_name)
    os.environ.setdefault("LITESTAR_GRANIAN_IN_SUBPROCESS", "false")
    os.environ.setdefault("LITESTAR_GRANIAN_USE_LITESTAR_LOGGER", "true")
    # original_format_help = LitestarExtensionGroup.format_help

    # def fixed_format_help(self: Any, ctx: Any, formatter: Any) -> None:
    #     """Ensure plugins are loaded before formatting help.

    #     Args:
    #         self: The LitestarExtensionGroup instance
    #         ctx: The click Context
    #         formatter: The help formatter
    #     """
    #     self._prepare(ctx)
    #     return original_format_help(self, ctx, formatter)

    # LitestarExtensionGroup.format_help = fixed_format_help

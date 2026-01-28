from __future__ import annotations

import logging
from collections import defaultdict
from uuid import UUID

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from app.domains.public.schemas.session import Session

from app.db import models as m

from litestar.params import Dependency, Parameter
from advanced_alchemy.extensions.litestar import filters, providers, service

from typing import Annotated

logger = logging.getLogger(__name__)

from app.domains.public.services.session import SessionService


class SessionController(Controller):
    """Public endpoints for caregivers (no auth required)."""

    path = "/api/v1"
    tags = ["Public"]
    dependencies = providers.create_service_dependencies(
        SessionService,
        "sessions_service",
        load=[m.Session.block_links],
        filters={"pagination_type": "limit_offset"},
    )

    @get("/sessions", status_code=HTTP_200_OK, summary="List sessions")
    async def list_sessions(
        self,
        sessions_service: SessionService,
        filters: Annotated[list[filters.FilterTypes], Dependency(skip_validation=True)],
    ) -> service.OffsetPagination[Session]:
        """List active public sessions sorted by region.

        Returns only non-archived sessions with their block associations.
        """
        results, total = await sessions_service.list_and_count(*filters)
        return sessions_service.to_schema(
            results, total, filters=filters, schema_type=Session
        )

    @get("/session/{session_id:uuid}", status_code=HTTP_200_OK, summary="Get session")
    async def get_session(
        self,
        sessions_service: SessionService,
        session_id: UUID,
    ) -> Session:
        """Fetch a session with public details."""
        session = await sessions_service.get(session_id)

        if not session:
            raise NotFoundException(detail="Session not found")

        return sessions_service.to_schema(session, schema_type=Session)

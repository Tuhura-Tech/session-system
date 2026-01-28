from __future__ import annotations

import logging
from uuid import UUID

from litestar import Controller, get, patch, post, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK


from app.domains.admin.schemas.session import Session, SessionCreate, SessionUpdate


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.session import SessionService

from litestar.params import Dependency, Parameter
from typing import Annotated
from advanced_alchemy.extensions.litestar import filters


class SessionController(Controller):
    """Admin endpoints for managing sessions."""

    path = "/api/v1/admin/sessions"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        SessionService,
        "session_service",
        # enable to filter by region, by min age, by max_age and by location
    )

    @get("/")
    async def list_sessions(
        self,
        session_service: SessionService,
    ) -> service.OffsetPagination[Session]:
        """List all sessions."""
        results, total = await session_service.list_and_count()
        return session_service.to_schema(results, total, schema_type=Session)

    @get("/{session_id:uuid}")
    async def get_session(
        self,
        session_id: UUID,
        session_service: SessionService,
    ) -> Session:
        """Get a single session by ID."""
        session = await session_service.get(session_id)
        if not session:
            raise NotFoundException(detail="Session not found")
        return session_service.to_schema(session, schema_type=Session)

    @post("/")
    async def create_session(
        self,
        session_data: SessionCreate,
        session_service: SessionService,
    ) -> Session:
        """Create a new session."""
        session = await session_service.create(session_data)
        return session_service.to_schema(session, schema_type=Session)

    @patch("/{session_id:uuid}")
    async def update_session(
        self,
        session_id: UUID,
        session_data: SessionUpdate,
        session_service: SessionService,
    ) -> Session:
        """Update an existing session."""
        session = await session_service.update(session_id, session_data)
        if not session:
            raise NotFoundException(detail="Session not found")
        return session_service.to_schema(session, schema_type=Session)

    @delete("/{session_id:uuid}", status_code=HTTP_200_OK)
    async def delete_session(
        self,
        session_id: UUID,
        session_service: SessionService,
    ) -> None:
        """Delete a session."""
        deleted = await session_service.delete(session_id)
        if not deleted:
            raise NotFoundException(detail="Session not found")

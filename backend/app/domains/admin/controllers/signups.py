from __future__ import annotations

import logging
from uuid import UUID

from litestar import Controller, get, patch, post, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK


from app.domains.admin.schemas.signup import Signup, SignupCreate, SignupUpdate


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.signup import SignupService

from litestar.params import Dependency, Parameter
from typing import Annotated
from advanced_alchemy.extensions.litestar import filters


class SignupController(Controller):
    """Admin endpoints for managing signups."""

    path = "/api/v1/admin/signups"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        SignupService,
        "signup_service",
        # enable to filter by region, by min age, by max_age and by location
    )

    @get("/{signup_id:uuid}")
    async def get_signup(
        self,
        signup_id: UUID,
        signup_service: SignupService,
    ) -> Signup:
        """Get a single signup by ID."""
        signup = await signup_service.get(signup_id)
        if not signup:
            raise NotFoundException(detail="Signup not found")
        return signup_service.to_schema(signup, schema_type=Signup)

    @patch("/{signup_id:uuid}")
    async def update_signup(
        self,
        signup_id: UUID,
        signup_data: SignupUpdate,
        signup_service: SignupService,
    ) -> Signup:
        """Update an existing signup."""
        signup = await signup_service.update(signup_id, signup_data)
        if not signup:
            raise NotFoundException(detail="Signup not found")
        return signup_service.to_schema(signup, schema_type=Signup)

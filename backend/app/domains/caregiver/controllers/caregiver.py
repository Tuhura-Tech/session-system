from __future__ import annotations
import logging

from litestar import Controller, get
from litestar.di import Provide
from litestar.status_codes import HTTP_200_OK


from app.domains.caregiver.schemas.caregiver import CaregiverMe

from app.db import models as m

logger = logging.getLogger(__name__)

from app.domains.caregiver.services.caregiver import CaregiverService

from app.domains.caregiver.deps import provide_caregiver_service


class CaregiverController(Controller):
    """Authenticated caregiver endpoints (profile, children, signups)."""

    path = "/api/v1"
    tags = ["Caregiver"]
    dependencies = {
        "caregiver_service": Provide(provide_caregiver_service),
    }

    @get("/me", status_code=HTTP_200_OK, summary="Get current caregiver")
    async def me(
        self, caregiver_service: CaregiverService, current_caregiver: m.Caregiver
    ) -> CaregiverMe:
        """Return the currently authenticated caregiver profile."""
        return caregiver_service.to_schema(current_caregiver, schema_type=CaregiverMe)

    # @patch("/me", status_code=HTTP_200_OK, summary="Update caregiver profile")
    # async def update_me(
    #     self, request: Request, db: AsyncSession, data: CaregiverUpdate
    # ) -> CaregiverMe:
    #     """Update caregiver name and phone number."""
    #     caregiver = await get_current_caregiver(request, db)
    #     assert caregiver is not None  # Required by dependency
    #     caregiver.name = data.name
    #     caregiver.phone = data.phone
    #     if data.referral_source:
    #         caregiver.referral_source = data.referral_source
    #     await db.flush()

    #     if data.subscribe_newsletter:
    #         queue = get_queue()
    #         await queue.enqueue(
    #             "notify_newsletter_subscription_task",
    #             email=caregiver.email,
    #             name=caregiver.name,
    #         )

    #     return CaregiverMe(
    #         id=str(caregiver.id),
    #         email=caregiver.email,
    #         name=caregiver.name,
    #         phone=caregiver.phone,
    #         email_verified=caregiver.email_verified,
    #         profile_complete=bool(caregiver.name and caregiver.phone),
    #     )

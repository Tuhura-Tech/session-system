# from __future__ import annotations

# import logging
# import uuid
# from zoneinfo import ZoneInfo

# from litestar import Controller, get, patch, post
# from litestar import delete as http_delete
# from litestar.di import Provide
# from litestar.exceptions import NotFoundException, ValidationException
# from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# logger = logging.getLogger(__name__)

# from app.admin_auth import admin_session_guard
# from app.db import get_db_session
# from app.db.models.exclusion_date import ExclusionDate
# from app.schemas.admin import (
#     ExclusionDateCreate,
#     ExclusionDateOut,
#     ExclusionDateUpdate,
# )

# TZ = ZoneInfo("Pacific/Auckland")


# def _ensure_uuid(s: str, *, field: str) -> uuid.UUID:
#     try:
#         return uuid.UUID(s)
#     except Exception:
#         raise ValidationException(detail=f"Invalid {field}")


# class AdminExclusionController(Controller):
#     """Admin/staff API.

#     These endpoints are protected by the admin session guard and are intended to be
#     used by the Astro admin UI.
#     """

#     path = "/api/v1/admin/exclusions"
#     dependencies = {"db": Provide(get_db_session)}
#     guards = [admin_session_guard]

#     @get(
#         "/",
#         status_code=HTTP_200_OK,
#         summary="List exclusions",
#         tags=["Admin: Exclusions"],
#     )
#     async def list_exclusions(
#         self, db: AsyncSession, year: int
#     ) -> list[ExclusionDateOut]:
#         """List exclusion dates for a year (holidays/closures)."""
#         res = await db.execute(
#             select(ExclusionDate)
#             .where(ExclusionDate.year == int(year))
#             .order_by(ExclusionDate.exclusion_date.asc())
#         )
#         return [
#             ExclusionDateOut(
#                 id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason
#             )
#             for x in res.scalars().all()
#         ]

#     @post(
#         "/",
#         status_code=HTTP_201_CREATED,
#         summary="Create exclusion",
#         tags=["Admin: Exclusions"],
#     )
#     async def create_exclusion(
#         self, db: AsyncSession, data: ExclusionDateCreate
#     ) -> ExclusionDateOut:
#         """Create an exclusion date."""
#         x = ExclusionDate(
#             year=data.date.year, exclusion_date=data.date, reason=data.reason
#         )
#         db.add(x)
#         await db.flush()
#         return ExclusionDateOut(
#             id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason
#         )

#     @patch(
#         "/{exclusion_id:uuid}",
#         status_code=HTTP_200_OK,
#         summary="Update exclusion",
#         tags=["Admin: Exclusions"],
#     )
#     async def update_exclusion(
#         self, db: AsyncSession, exclusion_id: uuid.UUID, data: ExclusionDateUpdate
#     ) -> ExclusionDateOut:
#         """Update an exclusion date (reason)."""
#         x = await db.get(ExclusionDate, exclusion_id)
#         if not x:
#             raise NotFoundException(detail="Exclusion not found")
#         x.reason = data.reason
#         await db.flush()
#         return ExclusionDateOut(
#             id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason
#         )

#     @http_delete(
#         "/{exclusion_id:uuid}",
#         status_code=HTTP_204_NO_CONTENT,
#         summary="Delete exclusion",
#         tags=["Admin: Exclusions"],
#     )
#     async def delete_exclusion(self, db: AsyncSession, exclusion_id: uuid.UUID) -> None:
#         """Delete an exclusion date."""
#         x = await db.get(ExclusionDate, exclusion_id)
#         if not x:
#             raise NotFoundException(detail="Exclusion not found")
#         await db.delete(x)
#         await db.commit()

#     @get(
#         "/{location_id:uuid}/sessions",
#         status_code=HTTP_200_OK,
#         summary="List sessions for a location",
#         tags=["Admin: Locations"],
#     )
#     async def list_location_sessions(
#         self,
#         db: AsyncSession,
#         location_id: uuid.UUID,
#         year: int | None = None,
#         include_archived: bool = False,
#     ) -> list[SessionOut]:
#         """List sessions at a specific location, optionally filtered by year and archived flag."""
#         stmt = (
#             select(Session)
#             .where(Session.session_location_id == location_id)
#             .options(selectinload(Session.block_links))
#         )
#         if year is not None:
#             stmt = stmt.where(Session.year == int(year))
#         if not include_archived:
#             stmt = stmt.where(Session.archived.is_(False))
#         stmt = stmt.order_by(Session.year.asc(), Session.name.asc())
#         res = await db.execute(stmt)
#         return [
#             SessionOut(
#                 id=str(s.id),
#                 sessionLocationId=str(s.session_location_id),
#                 year=s.year,
#                 session_type=s.session_type,
#                 name=s.name,
#                 ageLower=s.age_lower,
#                 ageUpper=s.age_upper,
#                 dayOfWeek=s.day_of_week,
#                 startTime=s.start_time,
#                 endTime=s.end_time,
#                 waitlist=s.waitlist,
#                 capacity=s.capacity,
#                 whatToBring=s.what_to_bring,
#                 prerequisites=s.prerequisites,
#                 photoAlbumUrl=s.photo_album_url,
#                 internalNotes=s.internal_notes,
#                 archived=s.archived,
#                 blockIds=[str(bl.block_id) for bl in s.block_links],
#             )
#             for s in res.scalars().all()
#         ]

from __future__ import annotations

import logging
from uuid import UUID

from litestar import Controller, get, patch, post, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK


from app.domains.admin.schemas.exclusion import (
    ExclusionDate,
    ExclusionDateCreate,
    ExclusionDateUpdate,
)


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.exclusion import ExclusionService


class ExclusionController(Controller):
    """Public endpoints for caregivers (no auth required)."""

    path = "/api/v1/admin/exclusions"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        ExclusionService,
        "exclusion_service",
    )

    @get("/", status_code=HTTP_200_OK, summary="List locations")
    async def list_exclusions(
        self,
        exclusion_service: ExclusionService,
    ) -> service.OffsetPagination[ExclusionDate]:
        """List active public sessions sorted by region.

        Returns only non-archived sessions with their block associations.
        """
        results, total = await exclusion_service.list_and_count()
        return exclusion_service.to_schema(results, schema_type=ExclusionDate)

    @post("/")
    async def create_exclusion(
        self,
        exclusion_service: ExclusionService,
        data: ExclusionDateCreate,
    ) -> ExclusionDate:
        """Create a new exclusion date."""
        exclusion = await exclusion_service.create(data)
        return exclusion_service.to_schema(exclusion, schema_type=ExclusionDate)

    @get(
        "/{exclusion_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Get exclusion date by ID",
    )
    async def get_exclusion(
        self,
        exclusion_service: ExclusionService,
        exclusion_id: UUID,
    ) -> ExclusionDate:
        """Get a specific exclusion date by ID."""
        exclusion = await exclusion_service.get(exclusion_id)
        if not exclusion:
            raise NotFoundException(detail="Exclusion date not found")

        return exclusion_service.to_schema(exclusion, schema_type=ExclusionDate)

    @patch(
        "/{exclusion_id:uuid}", status_code=HTTP_200_OK, summary="Update exclusion date"
    )
    async def update_exclusion(
        self,
        exclusion_service: ExclusionService,
        exclusion_id: UUID,
        data: ExclusionDateUpdate,
    ) -> ExclusionDate:
        """Update an existing exclusion date."""
        exclusion = await exclusion_service.update(
            data.model_dump(exclude_unset=True), exclusion_id
        )
        if not exclusion:
            raise NotFoundException(detail="Exclusion date not found")
        return exclusion_service.to_schema(exclusion, schema_type=ExclusionDate)

    @delete(
        "/{exclusion_id:uuid}", status_code=HTTP_200_OK, summary="Delete exclusion date"
    )
    async def delete_exclusion(
        self,
        exclusion_service: ExclusionService,
        exclusion_id: UUID,
    ) -> None:
        """Delete an exclusion date."""
        exclusion = await exclusion_service.get(exclusion_id)
        if not exclusion:
            raise NotFoundException(detail="Exclusion date not found")
        await exclusion_service.delete(exclusion_id)

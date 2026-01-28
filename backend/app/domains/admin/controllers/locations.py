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

from litestar import Controller, get, patch, post
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK


from app.domains.admin.schemas.location import Location, LocationCreate, LocationUpdate


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.location import LocationService


class LocationController(Controller):
    """Public endpoints for caregivers (no auth required)."""

    path = "/api/v1/admin/locations"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        LocationService,
        "location_service",
    )

    @get("/", status_code=HTTP_200_OK, summary="List locations")
    async def list_locations(
        self,
        location_service: LocationService,
    ) -> service.OffsetPagination[Location]:
        """List active public sessions sorted by region.

        Returns only non-archived sessions with their block associations.
        """
        results, total = await location_service.list_and_count()
        return location_service.to_schema(results, schema_type=Location)

    @post("/")
    async def create_location(
        self,
        location_service: LocationService,
        data: LocationCreate,
    ) -> Location:
        """Create a new location."""
        loc = await location_service.create(data)
        return location_service.to_schema(loc, schema_type=Location)

    @get("/{location_id:uuid}", status_code=HTTP_200_OK, summary="Get location by ID")
    async def get_location(
        self,
        location_service: LocationService,
        location_id: UUID,
    ) -> Location:
        """Get a specific location by ID."""
        loc = await location_service.get(location_id)
        if not loc:
            raise NotFoundException(detail="Location not found")

        return location_service.to_schema(loc, schema_type=Location)

    @patch("/{location_id:uuid}", status_code=HTTP_200_OK, summary="Update location")
    async def update_location(
        self,
        location_service: LocationService,
        location_id: UUID,
        data: LocationUpdate,
    ) -> Location:
        """Update an existing location."""
        loc = await location_service.update(
            data.model_dump(exclude_unset=True), location_id
        )
        if not loc:
            raise NotFoundException(detail="Location not found")
        return location_service.to_schema(loc, schema_type=Location)

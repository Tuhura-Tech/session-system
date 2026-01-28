# from __future__ import annotations

# import logging
# import uuid
# from zoneinfo import ZoneInfo

# from litestar import Controller, get, patch, post
# from litestar.di import Provide
# from litestar.exceptions import NotFoundException, ValidationException
# from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession

# logger = logging.getLogger(__name__)

# from app.admin_auth import admin_session_guard
# from app.db import get_db_session
# from app.db.models.session_block import SessionBlock
# from app.schemas.admin import (
#     SessionBlockCreate,
#     SessionBlockOut,
#     SessionBlockUpdate,
# )

# TZ = ZoneInfo("Pacific/Auckland")


# def _ensure_uuid(s: str, *, field: str) -> uuid.UUID:
#     try:
#         return uuid.UUID(s)
#     except Exception:
#         raise ValidationException(detail=f"Invalid {field}")


# class AdminBlockController(Controller):
#     """Admin/staff API.

#     These endpoints are protected by the admin session guard and are intended to be
#     used by the Astro admin UI.
#     """

#     path = "/api/v1/admin/blocks"
#     dependencies = {"db": Provide(get_db_session)}
#     guards = [admin_session_guard]

#     @get(
#         "/",
#         status_code=HTTP_200_OK,
#         summary="List blocks",
#         tags=["Admin: Blocks"],
#     )
#     async def list_blocks(
#         self, db: AsyncSession, year: int | None = None
#     ) -> list[SessionBlockOut]:
#         """List session blocks, optionally filtered by year."""
#         stmt = select(SessionBlock)
#         if year is not None:
#             stmt = stmt.where(SessionBlock.year == int(year))
#         stmt = stmt.order_by(SessionBlock.year.asc(), SessionBlock.start_date.asc())
#         res = await db.execute(stmt)
#         blocks = []
#         for b in res.scalars().all():
#             block_type_val = (
#                 b.block_type if isinstance(b.block_type, str) else b.block_type.value
#             )
#             blocks.append(
#                 SessionBlockOut(
#                     id=str(b.id),
#                     year=b.year,
#                     blockType=block_type_val,
#                     name=b.name,
#                     startDate=b.start_date,
#                     endDate=b.end_date,
#                     timezone=b.timezone,
#                 )
#             )
#         return blocks

#     @post(
#         "/",
#         status_code=HTTP_201_CREATED,
#         summary="Create block",
#         tags=["Admin: Blocks"],
#     )
#     async def create_block(
#         self, db: AsyncSession, data: SessionBlockCreate
#     ) -> SessionBlockOut:
#         """Create a new session block."""
#         block = SessionBlock(
#             year=data.year,
#             block_type=data.block_type,
#             name=data.name,
#             start_date=data.start_date,
#             end_date=data.end_date,
#             timezone=data.timezone,
#         )
#         db.add(block)
#         await db.flush()
#         block_type_val = (
#             block.block_type
#             if isinstance(block.block_type, str)
#             else block.block_type.value
#         )
#         return SessionBlockOut(
#             id=str(block.id),
#             year=block.year,
#             blockType=block_type_val,
#             name=block.name,
#             startDate=block.start_date,
#             endDate=block.end_date,
#             timezone=block.timezone,
#         )

#     @patch(
#         "/{block_id:uuid}",
#         status_code=HTTP_200_OK,
#         summary="Update block",
#         tags=["Admin: Blocks"],
#     )
#     async def update_block(
#         self, db: AsyncSession, block_id: uuid.UUID, data: SessionBlockUpdate
#     ) -> SessionBlockOut:
#         """Update an existing session block."""
#         block = await db.get(SessionBlock, block_id)
#         if not block:
#             raise NotFoundException(detail="Block not found")

#         if data.name is not None:
#             block.name = data.name
#         if data.start_date is not None:
#             block.start_date = data.start_date
#         if data.end_date is not None:
#             block.end_date = data.end_date
#         if data.timezone is not None:
#             block.timezone = data.timezone

#         await db.flush()
#         block_type_val = (
#             block.block_type
#             if isinstance(block.block_type, str)
#             else block.block_type.value
#         )
#         return SessionBlockOut(
#             id=str(block.id),
#             year=block.year,
#             blockType=block_type_val,
#             name=block.name,
#             startDate=block.start_date,
#             endDate=block.end_date,
#             timezone=block.timezone,
#         )
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


from app.domains.admin.schemas.block import Block, BlockCreate, BlockUpdate


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.block import BlockService


class BlockController(Controller):
    """Public endpoints for caregivers (no auth required)."""

    path = "/api/v1/admin/block"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        BlockService,
        "block_service",
    )

    @get("/", status_code=HTTP_200_OK, summary="List blocks")
    async def list_blocks(
        self,
        block_service: BlockService,
    ) -> service.OffsetPagination[Block]:
        """List active public sessions sorted by region.

        Returns only non-archived sessions with their block associations.
        """
        results, total = await block_service.list_and_count()
        return block_service.to_schema(results, schema_type=Block)

    @post("/")
    async def create_block(
        self,
        block_service: BlockService,
        data: BlockCreate,
    ) -> Block:
        """Create a new block."""
        blk = await block_service.create(data)
        return block_service.to_schema(blk, schema_type=Block)

    @get("/{block_id:uuid}", status_code=HTTP_200_OK, summary="Get block by ID")
    async def get_block(
        self,
        block_service: BlockService,
        block_id: UUID,
    ) -> Block:
        """Get a specific block by ID."""
        blk = await block_service.get(block_id)
        if not blk:
            raise NotFoundException(detail="Block not found")

        return block_service.to_schema(blk, schema_type=Block)

    @patch("/{block_id:uuid}", status_code=HTTP_200_OK, summary="Update block")
    async def update_block(
        self,
        block_service: BlockService,
        block_id: UUID,
        data: BlockUpdate,
    ) -> Block:
        """Update an existing block."""
        blk = await block_service.update(data.model_dump(exclude_unset=True), block_id)
        if not blk:
            raise NotFoundException(detail="Block not found")
        return block_service.to_schema(blk, schema_type=Block)

import logging
from collections import defaultdict
from datetime import UTC
from uuid import UUID

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db import get_db_session
from app.models.session import Session
from app.models.session_block import SessionBlock
from app.models.session_block_link import SessionBlockLink
from app.models.session_occurrence import SessionOccurrence
from app.models.views import SessionOccurrencePublicView
from app.schemas.session import (
    SessionPublic,
    SessionPublicDetail,
    SessionRegionGroup,
)
from app.services.calendar import build_session_calendar_feed

logger = logging.getLogger(__name__)


class PublicController(Controller):
    """Public endpoints for caregivers (no auth required)."""

    path = "/api/v1"
    tags = ["Public"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/sessions", status_code=HTTP_200_OK, summary="List sessions")
    async def list_sessions(
        self,
        db: AsyncSession,
        q: str | None = None,
    ) -> list[SessionRegionGroup]:
        """List active public sessions sorted by region.

        Returns only non-archived sessions with their block associations.
        """
        # Load sessions with location
        stmt = (
            select(Session)
            .options(selectinload(Session.session_location))
            .where(~Session.archived)  # Only active sessions
        )

        if q:
            # Search in session name (simplified for cross-database compatibility)
            search_term = f"%{q}%"
            stmt = stmt.where(Session.name.ilike(search_term))

        result = await db.execute(stmt)
        sessions = result.unique().scalars().all()

        # Load block info for each session via SQLAlchemy ORM (database-agnostic)
        if sessions:
            # Pre-load the block relationships using standard SQLAlchemy with eager loading
            stmt_blocks = (
                select(SessionBlockLink.session_id, SessionBlock.name)
                .join(SessionBlock, SessionBlock.id == SessionBlockLink.block_id)
                .where(SessionBlockLink.session_id.in_([s.id for s in sessions]))
            )
            block_result = await db.execute(stmt_blocks)
            blocks_by_session = defaultdict(list)

            for session_id, block_name in block_result.all():
                blocks_by_session[str(session_id)].append(block_name)

            # Attach blocks to sessions
            for session in sessions:
                session._blocks = blocks_by_session.get(str(session.id), [])

        grouped: dict[str, list[SessionPublic]] = defaultdict(list)
        for session in sessions:
            region = session.session_location.region if session.session_location else "Unknown"
            # Pass blocks to schema
            blocks = getattr(session, "_blocks", [])
            public_session = SessionPublic.from_orm_model(session, blocks=blocks)
            grouped[region].append(public_session)

        sorted_groups = sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)
        return [SessionRegionGroup(name=region_name, sessions=sessions) for region_name, sessions in sorted_groups]

    @get("/session/{session_id:uuid}", status_code=HTTP_200_OK, summary="Get session")
    async def get_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> SessionPublicDetail:
        """Fetch a session with full public details, including occurrences grouped by block."""
        from app.schemas.session import BlockOccurrences, SessionOccurrencePublic

        session_res = await db.execute(
            select(Session).options(selectinload(Session.session_location)).where(Session.id == session_id)
        )
        session = session_res.scalar_one_or_none()

        if not session or session.archived:
            raise NotFoundException(detail="Session not found")

        # Load blocks for this session (block id, name, type)
        blocks_res = await db.execute(
            select(
                SessionBlockLink.block_id,
                SessionBlock.name,
                SessionBlock.block_type,
            )
            .join(SessionBlock, SessionBlock.id == SessionBlockLink.block_id)
            .where(SessionBlockLink.session_id == session_id)
            .order_by(SessionBlockLink.block_id)
        )
        block_rows = blocks_res.all()

        # Load all occurrences for this session
        occurrences_res = await db.execute(
            select(SessionOccurrence)
            .where(SessionOccurrence.session_id == session_id)
            .order_by(SessionOccurrence.starts_at)
        )
        all_occurrences = occurrences_res.scalars().all()

        # Group occurrences by block
        occurrences_by_block_id = defaultdict(list)
        for occ in all_occurrences:
            if occ.block_id:
                occurrences_by_block_id[str(occ.block_id)].append(occ)

        # Build the response
        block_names: list[str] = []
        occurrences_by_block: list[BlockOccurrences] = []

        for block_id, block_name, block_type in block_rows:
            block_names.append(block_name)
            block_occurrences = occurrences_by_block_id.get(str(block_id), [])
            occurrences_by_block.append(
                BlockOccurrences(
                    block_id=str(block_id),
                    block_name=block_name,
                    block_type=block_type,
                    occurrences=[
                        SessionOccurrencePublic(
                            starts_at=occ.starts_at,
                            ends_at=occ.ends_at,
                            cancelled=occ.cancelled or False,
                            cancellation_reason=occ.cancellation_reason,
                        )
                        for occ in block_occurrences
                    ],
                )
            )

        return SessionPublicDetail.from_orm_model(
            session, blocks=block_names, occurrences_by_block=occurrences_by_block
        )

    @get(
        "/session/{session_id:uuid}/calendar.ics",
        status_code=HTTP_200_OK,
        summary="Download session calendar",
    )
    async def get_session_calendar(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> Response:
        """Generate an iCal (.ics) calendar for all session occurrences.

        This endpoint provides a calendar subscription URL that can be added to calendar apps.
        The calendar will automatically update when session times change or are cancelled.

        Compatible with:
        - Google Calendar (Add by URL)
        - Apple Calendar (File > New Calendar Subscription)
        - Outlook (Add Calendar > From Internet)
        - Any iCal-compatible calendar application

        The feed refreshes every 24 hours by default.
        """
        session_res = await db.execute(
            select(Session).options(selectinload(Session.session_location)).where(Session.id == session_id)
        )
        session = session_res.scalar_one_or_none()

        if not session or session.archived:
            raise NotFoundException(detail="Session not found")

        # Default to Pacific/Auckland for the calendar timezone
        tzid = "Pacific/Auckland"
        try:
            from zoneinfo import ZoneInfo

            tz = ZoneInfo(tzid)
        except Exception:
            tz = UTC
            tzid = "UTC"

        # Get all occurrences (including cancelled ones, which will be marked as CANCELLED)
        from datetime import datetime

        now = datetime.now(tz)
        occ_res = await db.execute(
            select(SessionOccurrencePublicView).where(SessionOccurrencePublicView.session_id == session_id)
        )
        occs = occ_res.scalars().all()

        # Only include future and recent past occurrences (last 7 days)
        from datetime import timedelta

        def _ensure_aware(dt: datetime) -> datetime:
            # SQLite may return naive datetimes even when timezone=True.
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

        cutoff = now - timedelta(days=7)
        relevant_occs = [o for o in occs if _ensure_aware(o.starts_at) >= cutoff]

        # Sort by start time
        relevant_occs.sort(key=lambda o: _ensure_aware(o.starts_at))

        # Convert to the format expected by build_session_calendar_feed
        # (start, end, cancelled, cancellation_reason)
        def _to_tz(dt: datetime) -> datetime:
            return _ensure_aware(dt).astimezone(tz)

        occurrence_data = [
            (
                _to_tz(o.starts_at) if tz else o.starts_at,
                _to_tz(o.ends_at) if tz else o.ends_at,
                getattr(o, "cancelled", False),
                getattr(o, "cancellation_reason", None),
            )
            for o in relevant_occs
        ]

        venue = getattr(session, "location_name", None) or session.name
        address = getattr(session, "location_address", None) or ""
        location = f"{venue} - {address}" if address else venue
        url = f"{settings.public_base_url}/sessions/{session.id}"

        ics_text = build_session_calendar_feed(
            session_id=str(session.id),
            session_name=session.name,
            occurrences=occurrence_data,
            location=location,
            address=address,
            tzid=tzid,
            url=url,
            refresh_interval_hours=24,
        )

        return Response(
            content=ics_text,
            media_type="text/calendar; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="session-{session.id}.ics"',
                "Cache-Control": "public, max-age= 86400",  # Cache for 1 day
            },
        )

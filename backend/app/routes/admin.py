from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from litestar import Controller, get, patch, post
from litestar import delete as http_delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException, ValidationException
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings

logger = logging.getLogger(__name__)
from typing import cast

from app.admin_auth import admin_session_guard
from app.db import get_db_session
from app.models.attendance import AttendanceRecord
from app.models.attendance_audit import AttendanceAuditLog
from app.models.child_note import ChildNote
from app.models.exclusion_date import ExclusionDate
from app.models.session import DayOfWeekEnum, Session
from app.models.session_block import SessionBlock
from app.models.session_block_link import SessionBlockLink
from app.models.session_location import SessionLocation
from app.models.session_occurrence import SessionOccurrence
from app.models.signup import Signup
from app.models.views import CaregiverStaffView, ChildStaffView
from app.schemas.admin import (
    AdminSignupOut,
    AttendanceRecordOut,
    AttendanceRollItem,
    AttendanceRollOut,
    AttendanceStatus,
    AttendanceUpsert,
    BulkEmailRequest,
    ChildAdminOut,
    ChildNoteCreate,
    ChildNoteOut,
    ExclusionDateCreate,
    ExclusionDateOut,
    ExclusionDateUpdate,
    OccurrenceCancel,
    OccurrenceCreate,
    OccurrenceOut,
    SessionBlockCreate,
    SessionBlockOut,
    SessionBlockUpdate,
    SessionChangeAlertRequest,
    SessionCreate,
    SessionLocationCreate,
    SessionLocationOut,
    SessionLocationUpdate,
    SessionOut,
    SessionUpdate,
    SignupStatusUpdate,
)
from app.schemas.session import _format_time_range
from app.worker import get_queue

TZ = ZoneInfo("Pacific/Auckland")


def _fmt_local_datetime(dt: datetime) -> str:
    return dt.astimezone(TZ).strftime("%a %d %b %Y, %-I:%M%p")


async def _notify_confirmed_signups(
    *,
    db: AsyncSession,
    queue,
    session: Session,
    update_title: str,
    update_message: str | None,
    affected_date: str | None,
) -> int:
    res = await db.execute(
        select(Signup, CaregiverStaffView, ChildStaffView)
        .join(CaregiverStaffView, Signup.caregiver_id == CaregiverStaffView.id)
        .join(ChildStaffView, Signup.child_id == ChildStaffView.id)
        .where(Signup.session_id == session.id, Signup.status == "confirmed")
        .order_by(Signup.created_at.asc())
    )
    rows = res.all()

    loc = getattr(session, "session_location", None)
    session_time = _format_time_range(session.day_of_week, session.start_time, session.end_time)
    session_venue = getattr(loc, "name", None)
    session_address = getattr(loc, "address", None)

    enqueued = 0
    for su, caregiver, child in rows:
        if not caregiver.email or not caregiver.name:
            continue
        await queue.enqueue(
            "send_session_change_alert_task",
            to_email=caregiver.email,
            caregiver_name=caregiver.name,
            child_name=child.name,
            session_name=session.name,
            session_venue=session_venue,
            session_address=session_address,
            session_time=session_time,
            update_title=update_title,
            update_message=update_message,
            affected_date=affected_date,
        )
        enqueued += 1
    return enqueued


def _dt_at_local(d: datetime) -> datetime:
    return d.astimezone(TZ)


def _combine_local_date_time(d, t) -> datetime:
    return datetime.combine(d, t, tzinfo=TZ)


def _ensure_uuid(s: str, *, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(s)
    except Exception:
        raise ValidationException(detail=f"Invalid {field}")


async def _enqueue_custom_bulk_email(
    *,
    queue,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session: Session,
    subject: str,
    message: str,
) -> None:
    # Use the existing session_change_alert template for admin bulk comms.
    loc = getattr(session, "session_location", None)
    await queue.enqueue(
        "send_session_change_alert_task",
        to_email=to_email,
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session.name,
        session_venue=getattr(loc, "name", None),
        session_address=getattr(loc, "address", None),
        session_time=_format_time_range(session.day_of_week, session.start_time, session.end_time),
        update_title=subject,
        update_message=message,
        affected_date=None,
        contact_email=getattr(loc, "contact_email", None),
    )


class AdminController(Controller):
    """Admin/staff API.

    These endpoints are protected by the admin session guard and are intended to be
    used by the Astro admin UI.
    """

    path = "/api/v1/admin"
    dependencies = {"db": Provide(get_db_session)}
    guards = [admin_session_guard]

    # ---------- Blocks ----------

    @get(
        "/blocks",
        status_code=HTTP_200_OK,
        summary="List blocks",
        tags=["Admin: Blocks"],
    )
    async def list_blocks(self, db: AsyncSession, year: int | None = None) -> list[SessionBlockOut]:
        """List session blocks, optionally filtered by year."""
        stmt = select(SessionBlock)
        if year is not None:
            stmt = stmt.where(SessionBlock.year == int(year))
        stmt = stmt.order_by(SessionBlock.year.asc(), SessionBlock.start_date.asc())
        res = await db.execute(stmt)
        blocks = []
        for b in res.scalars().all():
            block_type_val = b.block_type if isinstance(b.block_type, str) else b.block_type.value
            blocks.append(
                SessionBlockOut(
                    id=str(b.id),
                    year=b.year,
                    blockType=block_type_val,
                    name=b.name,
                    startDate=b.start_date,
                    endDate=b.end_date,
                    timezone=b.timezone,
                )
            )
        return blocks

    @post(
        "/blocks",
        status_code=HTTP_201_CREATED,
        summary="Create block",
        tags=["Admin: Blocks"],
    )
    async def create_block(self, db: AsyncSession, data: SessionBlockCreate) -> SessionBlockOut:
        """Create a new session block."""
        block = SessionBlock(
            year=data.year,
            block_type=data.block_type,
            name=data.name,
            start_date=data.start_date,
            end_date=data.end_date,
            timezone=data.timezone,
        )
        db.add(block)
        await db.flush()
        block_type_val = block.block_type if isinstance(block.block_type, str) else block.block_type.value
        return SessionBlockOut(
            id=str(block.id),
            year=block.year,
            blockType=block_type_val,
            name=block.name,
            startDate=block.start_date,
            endDate=block.end_date,
            timezone=block.timezone,
        )

    @patch(
        "/blocks/{block_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Update block",
        tags=["Admin: Blocks"],
    )
    async def update_block(self, db: AsyncSession, block_id: uuid.UUID, data: SessionBlockUpdate) -> SessionBlockOut:
        """Update an existing session block."""
        block = await db.get(SessionBlock, block_id)
        if not block:
            raise NotFoundException(detail="Block not found")

        if data.name is not None:
            block.name = data.name
        if data.start_date is not None:
            block.start_date = data.start_date
        if data.end_date is not None:
            block.end_date = data.end_date
        if data.timezone is not None:
            block.timezone = data.timezone

        await db.flush()
        block_type_val = block.block_type if isinstance(block.block_type, str) else block.block_type.value
        return SessionBlockOut(
            id=str(block.id),
            year=block.year,
            blockType=block_type_val,
            name=block.name,
            startDate=block.start_date,
            endDate=block.end_date,
            timezone=block.timezone,
        )

    # ---------- Exclusions ----------

    @get(
        "/exclusions",
        status_code=HTTP_200_OK,
        summary="List exclusions",
        tags=["Admin: Exclusions"],
    )
    async def list_exclusions(self, db: AsyncSession, year: int) -> list[ExclusionDateOut]:
        """List exclusion dates for a year (holidays/closures)."""
        res = await db.execute(
            select(ExclusionDate).where(ExclusionDate.year == int(year)).order_by(ExclusionDate.exclusion_date.asc())
        )
        return [
            ExclusionDateOut(id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason)
            for x in res.scalars().all()
        ]

    @post(
        "/exclusions",
        status_code=HTTP_201_CREATED,
        summary="Create exclusion",
        tags=["Admin: Exclusions"],
    )
    async def create_exclusion(self, db: AsyncSession, data: ExclusionDateCreate) -> ExclusionDateOut:
        """Create an exclusion date."""
        x = ExclusionDate(year=data.date.year, exclusion_date=data.date, reason=data.reason)
        db.add(x)
        await db.flush()
        return ExclusionDateOut(id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason)

    @patch(
        "/exclusions/{exclusion_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Update exclusion",
        tags=["Admin: Exclusions"],
    )
    async def update_exclusion(
        self, db: AsyncSession, exclusion_id: uuid.UUID, data: ExclusionDateUpdate
    ) -> ExclusionDateOut:
        """Update an exclusion date (reason)."""
        x = await db.get(ExclusionDate, exclusion_id)
        if not x:
            raise NotFoundException(detail="Exclusion not found")
        x.reason = data.reason
        await db.flush()
        return ExclusionDateOut(id=str(x.id), year=x.year, date=x.exclusion_date, reason=x.reason)

    @http_delete(
        "/exclusions/{exclusion_id:uuid}",
        status_code=HTTP_204_NO_CONTENT,
        summary="Delete exclusion",
        tags=["Admin: Exclusions"],
    )
    async def delete_exclusion(self, db: AsyncSession, exclusion_id: uuid.UUID) -> None:
        """Delete an exclusion date."""
        x = await db.get(ExclusionDate, exclusion_id)
        if not x:
            raise NotFoundException(detail="Exclusion not found")
        await db.delete(x)
        await db.commit()

    # ---------- Locations ----------

    @get(
        "/locations",
        status_code=HTTP_200_OK,
        summary="List locations",
        tags=["Admin: Locations"],
    )
    async def list_locations(self, db: AsyncSession) -> list[SessionLocationOut]:
        """List all session locations."""
        res = await db.execute(
            select(SessionLocation).order_by(SessionLocation.region.asc(), SessionLocation.name.asc())
        )
        out: list[SessionLocationOut] = []
        for loc in res.scalars().all():
            out.append(
                SessionLocationOut(
                    id=str(loc.id),
                    name=loc.name,
                    address=loc.address,
                    region=loc.region,
                    lat=loc.lat,
                    lng=loc.lng,
                    instructions=loc.instructions,
                    contactName=loc.contact_name,
                    contactEmail=loc.contact_email,
                    contactPhone=loc.contact_phone,
                    internalNotes=loc.internal_notes,
                )
            )
        return out

    @get(
        "/locations/{location_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Get location by ID",
        tags=["Admin: Locations"],
    )
    async def get_location(self, db: AsyncSession, location_id: uuid.UUID) -> SessionLocationOut:
        """Get a specific session location by ID."""
        loc = await db.get(SessionLocation, location_id)
        if not loc:
            raise NotFoundException(detail="Location not found")

        return SessionLocationOut(
            id=str(loc.id),
            name=loc.name,
            address=loc.address,
            region=loc.region,
            lat=loc.lat,
            lng=loc.lng,
            instructions=loc.instructions,
            contactName=loc.contact_name,
            contactEmail=loc.contact_email,
            contactPhone=loc.contact_phone,
            internalNotes=loc.internal_notes,
        )

    @post(
        "/locations",
        status_code=HTTP_201_CREATED,
        summary="Create location",
        tags=["Admin: Locations"],
    )
    async def create_location(self, db: AsyncSession, data: SessionLocationCreate) -> SessionLocationOut:
        """Create a new session location."""
        loc = SessionLocation(
            name=data.name,
            address=data.address,
            region=data.region,
            lat=data.lat,
            lng=data.lng,
            instructions=data.instructions,
            contact_name=data.contact_name,
            contact_email=str(data.contact_email),
            contact_phone=data.contact_phone,
            internal_notes=data.internal_notes,
        )
        db.add(loc)
        await db.flush()
        return SessionLocationOut(
            id=str(loc.id),
            name=loc.name,
            address=loc.address,
            region=loc.region,
            lat=loc.lat,
            lng=loc.lng,
            instructions=loc.instructions,
            contactName=loc.contact_name,
            contactEmail=loc.contact_email,
            contactPhone=loc.contact_phone,
            internalNotes=loc.internal_notes,
        )

    @patch(
        "/locations/{location_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Update location",
        tags=["Admin: Locations"],
    )
    async def update_location(
        self, db: AsyncSession, location_id: uuid.UUID, data: SessionLocationUpdate
    ) -> SessionLocationOut:
        """Update an existing session location."""
        loc = await db.get(SessionLocation, location_id)
        if not loc:
            raise NotFoundException(detail="Location not found")

        for attr in ["name", "address", "region", "lat", "lng", "instructions"]:
            v = getattr(data, attr)
            if v is not None:
                setattr(loc, attr, v)

        if data.contact_name is not None:
            loc.contact_name = data.contact_name
        if data.contact_email is not None:
            loc.contact_email = str(data.contact_email)
        if data.contact_phone is not None:
            loc.contact_phone = data.contact_phone
        if data.internal_notes is not None:
            loc.internal_notes = data.internal_notes

        await db.flush()
        return SessionLocationOut(
            id=str(loc.id),
            name=loc.name,
            address=loc.address,
            region=loc.region,
            lat=loc.lat,
            lng=loc.lng,
            instructions=loc.instructions,
            contactName=loc.contact_name,
            contactEmail=loc.contact_email,
            contactPhone=loc.contact_phone,
            internalNotes=loc.internal_notes,
        )

    # ---------- Sessions ----------

    @get(
        "/sessions",
        status_code=HTTP_200_OK,
        summary="List sessions",
        tags=["Admin: Sessions"],
    )
    async def list_sessions(
        self, db: AsyncSession, year: int | None = None, include_archived: bool = False
    ) -> list[SessionOut]:
        """List sessions.

        Optionally filter by `year` and include archived sessions.
        """
        from sqlalchemy.orm import selectinload

        stmt = select(Session).options(selectinload(Session.block_links))
        if year is not None:
            stmt = stmt.where(Session.year == int(year))
        if not include_archived:
            stmt = stmt.where(Session.archived.is_(False))
        stmt = stmt.order_by(Session.year.asc(), Session.name.asc())
        res = await db.execute(stmt)
        return [
            SessionOut(
                id=str(s.id),
                sessionLocationId=str(s.session_location_id),
                year=s.year,
                session_type=s.session_type,
                name=s.name,
                ageLower=s.age_lower,
                ageUpper=s.age_upper,
                dayOfWeek=s.day_of_week,
                startTime=s.start_time,
                endTime=s.end_time,
                waitlist=s.waitlist,
                capacity=s.capacity,
                whatToBring=s.what_to_bring,
                prerequisites=s.prerequisites,
                photoAlbumUrl=s.photo_album_url,
                internalNotes=s.internal_notes,
                archived=s.archived,
                blockIds=[str(bl.block_id) for bl in s.block_links],
            )
            for s in res.scalars().all()
        ]

    @get(
        "/sessions/{session_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Get session",
        tags=["Admin: Sessions"],
    )
    async def get_session(self, db: AsyncSession, session_id: uuid.UUID) -> SessionOut:
        """Get a single session by ID."""
        from sqlalchemy.orm import selectinload

        s = await db.get(Session, session_id, options=[selectinload(Session.block_links)])
        if not s:
            raise NotFoundException(detail="Session not found")

        return SessionOut(
            id=str(s.id),
            sessionLocationId=str(s.session_location_id),
            year=s.year,
            session_type=s.session_type,
            name=s.name,
            ageLower=s.age_lower,
            ageUpper=s.age_upper,
            dayOfWeek=s.day_of_week,
            startTime=s.start_time,
            endTime=s.end_time,
            waitlist=s.waitlist,
            capacity=s.capacity,
            whatToBring=s.what_to_bring,
            prerequisites=s.prerequisites,
            photoAlbumUrl=s.photo_album_url,
            internalNotes=s.internal_notes,
            archived=s.archived,
            blockIds=[str(bl.block_id) for bl in s.block_links],
        )

    @get(
        "/locations/{location_id:uuid}/sessions",
        status_code=HTTP_200_OK,
        summary="List sessions for a location",
        tags=["Admin: Locations"],
    )
    async def list_location_sessions(
        self, db: AsyncSession, location_id: uuid.UUID, year: int | None = None, include_archived: bool = False
    ) -> list[SessionOut]:
        """List sessions at a specific location, optionally filtered by year and archived flag."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Session).where(Session.session_location_id == location_id).options(selectinload(Session.block_links))
        )
        if year is not None:
            stmt = stmt.where(Session.year == int(year))
        if not include_archived:
            stmt = stmt.where(Session.archived.is_(False))
        stmt = stmt.order_by(Session.year.asc(), Session.name.asc())
        res = await db.execute(stmt)
        return [
            SessionOut(
                id=str(s.id),
                sessionLocationId=str(s.session_location_id),
                year=s.year,
                session_type=s.session_type,
                name=s.name,
                ageLower=s.age_lower,
                ageUpper=s.age_upper,
                dayOfWeek=s.day_of_week,
                startTime=s.start_time,
                endTime=s.end_time,
                waitlist=s.waitlist,
                capacity=s.capacity,
                whatToBring=s.what_to_bring,
                prerequisites=s.prerequisites,
                photoAlbumUrl=s.photo_album_url,
                internalNotes=s.internal_notes,
                archived=s.archived,
                blockIds=[str(bl.block_id) for bl in s.block_links],
            )
            for s in res.scalars().all()
        ]

    @post(
        "/sessions",
        status_code=HTTP_201_CREATED,
        summary="Create session",
        tags=["Admin: Sessions"],
    )
    async def create_session(self, db: AsyncSession, data: SessionCreate) -> SessionOut:
        """Create a new session."""
        loc_id = _ensure_uuid(data.session_location_id, field="sessionLocationId")
        s = Session(
            session_location_id=loc_id,
            year=data.year,
            session_type=data.session_type,
            name=data.name,
            age_lower=data.age_lower,
            age_upper=data.age_upper,
            day_of_week=data.day_of_week,
            start_time=data.start_time,
            end_time=data.end_time,
            waitlist=data.waitlist,
            capacity=data.capacity,
            what_to_bring=data.what_to_bring,
            prerequisites=data.prerequisites,
            photo_album_url=data.photo_album_url,
            internal_notes=data.internal_notes,
            archived=data.archived,
        )
        db.add(s)
        await db.flush()

        # Create block links
        for block_id_str in data.block_ids:
            block_id = _ensure_uuid(block_id_str, field="blockIds")
            db.add(SessionBlockLink(session_id=s.id, block_id=block_id))
        await db.flush()

        return SessionOut(
            session_type=s.session_type,
            id=str(s.id),
            sessionLocationId=str(s.session_location_id),
            year=s.year,
            name=s.name,
            ageLower=s.age_lower,
            ageUpper=s.age_upper,
            dayOfWeek=s.day_of_week,
            startTime=s.start_time,
            endTime=s.end_time,
            waitlist=s.waitlist,
            capacity=s.capacity,
            whatToBring=s.what_to_bring,
            prerequisites=s.prerequisites,
            photoAlbumUrl=s.photo_album_url,
            internalNotes=s.internal_notes,
            archived=s.archived,
            blockIds=data.block_ids,
        )

    @patch(
        "/sessions/{session_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Update session",
        tags=["Admin: Sessions"],
    )
    async def update_session(self, db: AsyncSession, session_id: uuid.UUID, data: SessionUpdate) -> SessionOut:
        """Update an existing session."""
        from sqlalchemy.orm import selectinload

        s = await db.get(Session, session_id, options=[selectinload(Session.block_links)])
        if not s:
            raise NotFoundException(detail="Session not found")

        if data.session_location_id is not None:
            s.session_location_id = _ensure_uuid(data.session_location_id, field="sessionLocationId")
        if data.year is not None:
            s.year = data.year
        new_session_type = data.session_type if data.session_type is not None else getattr(data, "sessionType", None)
        if new_session_type is not None:
            s.session_type = new_session_type

        for attr in [
            "name",
            "waitlist",
            "capacity",
            "archived",
            "prerequisites",
        ]:
            v = getattr(data, attr)
            if v is not None:
                setattr(s, attr, v)

        if data.age_lower is not None:
            s.age_lower = data.age_lower
        if data.age_upper is not None:
            s.age_upper = data.age_upper

        if data.day_of_week is not None:
            s.day_of_week = DayOfWeekEnum(data.day_of_week) if isinstance(data.day_of_week, int) else data.day_of_week
        if data.start_time is not None:
            s.start_time = data.start_time
        if data.end_time is not None:
            s.end_time = data.end_time

        if data.what_to_bring is not None:
            s.what_to_bring = data.what_to_bring
        if data.photo_album_url is not None:
            s.photo_album_url = data.photo_album_url
        if data.internal_notes is not None:
            s.internal_notes = data.internal_notes

        # Handle block_ids updates
        if data.block_ids is not None:
            await db.execute(delete(SessionBlockLink).where(SessionBlockLink.session_id == session_id))
            for block_id_str in data.block_ids:
                block_id = _ensure_uuid(block_id_str, field="blockIds")
                db.add(SessionBlockLink(session_id=s.id, block_id=block_id))

        await db.flush()
        await db.refresh(s, ["block_links"])

        return SessionOut(
            id=str(s.id),
            sessionLocationId=str(s.session_location_id),
            session_type=s.session_type,
            year=s.year,
            name=s.name,
            ageLower=s.age_lower,
            ageUpper=s.age_upper,
            dayOfWeek=s.day_of_week,
            startTime=s.start_time,
            endTime=s.end_time,
            waitlist=s.waitlist,
            capacity=s.capacity,
            whatToBring=s.what_to_bring,
            prerequisites=s.prerequisites,
            photoAlbumUrl=s.photo_album_url,
            internalNotes=s.internal_notes,
            archived=s.archived,
            blockIds=[str(bl.block_id) for bl in s.block_links],
        )

    @http_delete(
        "/sessions/{session_id:uuid}",
        status_code=HTTP_204_NO_CONTENT,
        summary="Delete session",
        tags=["Admin: Sessions"],
    )
    async def delete_session(self, db: AsyncSession, session_id: uuid.UUID) -> None:
        """Delete a session and all its associated data (occurrences, signups, etc)."""
        s = await db.get(Session, session_id)
        if not s:
            raise NotFoundException(detail="Session not found")

        await db.delete(s)
        await db.commit()

    @post(
        "/sessions/{session_id:uuid}/duplicate",
        status_code=HTTP_200_OK,
        summary="Duplicate session",
        tags=["Admin: Sessions"],
    )
    async def duplicate_session(self, db: AsyncSession, session_id: uuid.UUID) -> SessionOut:
        """Create a duplicate of an existing session (without occurrences or signups)."""
        from sqlalchemy.orm import selectinload

        s = await db.get(Session, session_id, options=[selectinload(Session.block_links)])
        if not s:
            raise NotFoundException(detail="Session not found")

        # Create new session with same attributes
        new_session = Session(
            session_location_id=s.session_location_id,
            year=s.year,
            name=f"{s.name} (Copy)",
            age_lower=s.age_lower,
            age_upper=s.age_upper,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            waitlist=s.waitlist,
            capacity=s.capacity,
            what_to_bring=s.what_to_bring,
            prerequisites=s.prerequisites,
            photo_album_url=s.photo_album_url,
            internal_notes=s.internal_notes,
            archived=s.archived,
        )
        db.add(new_session)
        await db.flush()

        # Copy block links
        for bl in s.block_links:
            new_link = SessionBlockLink(session_id=new_session.id, block_id=bl.block_id)
            db.add(new_link)

        await db.commit()
        await db.refresh(new_session, ["block_links"])

        return SessionOut(
            id=str(new_session.id),
            sessionLocationId=str(new_session.session_location_id),
            year=new_session.year,
            name=new_session.name,
            ageLower=new_session.age_lower,
            ageUpper=new_session.age_upper,
            dayOfWeek=new_session.day_of_week,
            startTime=new_session.start_time,
            endTime=new_session.end_time,
            waitlist=new_session.waitlist,
            capacity=new_session.capacity,
            whatToBring=new_session.what_to_bring,
            prerequisites=new_session.prerequisites,
            photoAlbumUrl=new_session.photo_album_url,
            internalNotes=new_session.internal_notes,
            archived=new_session.archived,
            blockIds=[str(bl.block_id) for bl in new_session.block_links],
        )

    # ---------- Occurrences ----------

    @post(
        "/sessions/{session_id:uuid}/occurrences/generate",
        status_code=HTTP_200_OK,
        summary="Generate occurrences",
        tags=["Admin: Occurrences"],
    )
    async def generate_occurrences(self, db: AsyncSession, session_id: uuid.UUID) -> dict:
        """Generate occurrences for a term session from linked blocks + exclusions.

        Only generates for blocks linked via session_block_links.
        Marks occurrences as auto_generated=True and assigns block_id.
        Idempotent: does not create duplicates.
        """
        s = await db.get(Session, session_id)
        if not s:
            raise NotFoundException(detail="Session not found")
        if s.session_type != "term":
            raise ValidationException(detail="Occurrence generation is for term sessions")
        if s.day_of_week is None or s.start_time is None or s.end_time is None:
            raise ValidationException(detail="Session schedule is incomplete")

        blocks_res = await db.execute(
            select(SessionBlock)
            .join(SessionBlockLink, SessionBlockLink.block_id == SessionBlock.id)
            .where(SessionBlockLink.session_id == s.id)
            .order_by(SessionBlock.start_date)
        )
        blocks = blocks_res.scalars().all()

        if not blocks:
            raise ValidationException(detail="No blocks selected for this session. Please add blocks first.")

        ex_res = await db.execute(select(ExclusionDate).where(ExclusionDate.year.in_({b.year for b in blocks})))
        excluded_by_year = {}
        for x in ex_res.scalars().all():
            excluded_by_year.setdefault(x.year, set()).add(x.exclusion_date)

        created = 0
        skipped_existing = 0

        for block in blocks:
            day = block.start_date
            days_ahead = (int(s.day_of_week) - day.weekday() + 7) % 7
            day = day + timedelta(days=days_ahead)

            excluded = excluded_by_year.get(block.year, set())

            while day <= block.end_date:
                if day not in excluded:
                    starts_at = _combine_local_date_time(day, s.start_time)
                    ends_at = _combine_local_date_time(day, s.end_time)

                    exists_res = await db.execute(
                        select(SessionOccurrence.id).where(
                            SessionOccurrence.session_id == s.id,
                            SessionOccurrence.starts_at == starts_at,
                        )
                    )
                    if exists_res.scalar_one_or_none():
                        skipped_existing += 1
                    else:
                        db.add(
                            SessionOccurrence(
                                session_id=s.id,
                                block_id=block.id,
                                starts_at=starts_at,
                                ends_at=ends_at,
                                auto_generated=True,
                            )
                        )
                        created += 1

                day = day + timedelta(days=7)

        await db.flush()
        return {"created": created, "skippedExisting": skipped_existing}

    @post(
        "/sessions/{session_id:uuid}/occurrences/regenerate",
        status_code=HTTP_200_OK,
        summary="Regenerate auto-generated occurrences",
        tags=["Admin: Occurrences"],
    )
    async def regenerate_occurrences(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        delete_auto_generated: bool = False,
    ) -> dict:
        """Regenerate occurrences for a term session.

        Options:
        - delete_auto_generated=False (default): Only adds missing occurrences
        - delete_auto_generated=True: Deletes all auto-generated occurrences and recreates them

        Manual occurrences (auto_generated=False) are never deleted.
        """
        s = await db.get(Session, session_id)
        if not s:
            raise NotFoundException(detail="Session not found")
        if s.session_type != "term":
            raise ValidationException(detail="Regeneration is for term sessions")

        deleted = 0
        if delete_auto_generated:
            # Delete only auto-generated occurrences
            result = await db.execute(
                delete(SessionOccurrence).where(
                    SessionOccurrence.session_id == session_id,
                    SessionOccurrence.auto_generated == True,  # noqa: E712
                )
            )
            deleted = getattr(result, "rowcount", 0) or 0
            await db.flush()

        # Manually generate occurrences (duplicating logic from generate_occurrences)
        stmt = (
            select(SessionBlock)
            .join(SessionBlockLink, SessionBlockLink.block_id == SessionBlock.id)
            .where(SessionBlockLink.session_id == session_id)
            .order_by(SessionBlock.start_date.asc())
        )
        blocks_res = await db.execute(stmt)
        blocks = list(blocks_res.scalars().all())

        if not blocks:
            raise ValidationException(detail="No blocks selected for this session. Please add blocks first.")

        exclusions_stmt = select(ExclusionDate).where(ExclusionDate.year.in_({b.year for b in blocks}))
        exclusions_res = await db.execute(exclusions_stmt)
        exclusion_dates_by_year = {}
        for ed in exclusions_res.scalars():
            exclusion_dates_by_year.setdefault(ed.year, set()).add(ed.exclusion_date)

        created = 0
        skipped_existing = 0

        for block in blocks:
            tz = ZoneInfo("Pacific/Auckland")
            day = block.start_date
            while day <= block.end_date:
                if (
                    s.day_of_week
                    and day.weekday() == s.day_of_week.value
                    and day not in exclusion_dates_by_year.get(block.year, set())
                ):
                    starts_at = datetime.combine(day, s.start_time, tzinfo=tz)
                    ends_at = datetime.combine(day, s.end_time, tzinfo=tz)

                    exists_res = await db.execute(
                        select(SessionOccurrence.id).where(
                            SessionOccurrence.session_id == s.id,
                            SessionOccurrence.starts_at == starts_at,
                        )
                    )
                    if exists_res.scalar_one_or_none():
                        skipped_existing += 1
                    else:
                        db.add(
                            SessionOccurrence(
                                session_id=s.id,
                                block_id=block.id,
                                starts_at=starts_at,
                                ends_at=ends_at,
                                auto_generated=True,
                            )
                        )
                        created += 1

                day = day + timedelta(days=7)

        await db.flush()

        return {
            "deleted": deleted,
            "created": created,
            "skippedExisting": skipped_existing,
        }

    @get(
        "/sessions/{session_id:uuid}/occurrences",
        status_code=HTTP_200_OK,
        summary="List occurrences",
        tags=["Admin: Occurrences"],
    )
    async def list_occurrences(self, db: AsyncSession, session_id: uuid.UUID) -> list[OccurrenceOut]:
        """List occurrences for a session."""
        res = await db.execute(
            select(SessionOccurrence, SessionBlock.name)
            .outerjoin(SessionBlock, SessionOccurrence.block_id == SessionBlock.id)
            .where(SessionOccurrence.session_id == session_id)
            .order_by(SessionOccurrence.starts_at.asc())
        )
        rows = res.all()
        return [
            OccurrenceOut(
                id=str(o.id),
                sessionId=str(o.session_id),
                startsAt=o.starts_at,
                endsAt=o.ends_at,
                cancelled=o.cancelled,
                cancellationReason=o.cancellation_reason,
                autoGenerated=o.auto_generated,
                blockId=str(o.block_id) if o.block_id else None,
                blockName=block_name,
            )
            for o, block_name in rows
        ]

    @post(
        "/sessions/{session_id:uuid}/occurrences",
        status_code=HTTP_200_OK,
        summary="Create occurrence",
        tags=["Admin: Occurrences"],
    )
    async def create_occurrence(self, db: AsyncSession, session_id: uuid.UUID, data: OccurrenceCreate) -> OccurrenceOut:
        """Create a one-off occurrence for a session (manual creation)."""
        s = await db.get(Session, session_id)
        if not s:
            raise NotFoundException(detail="Session not found")
        block_id = _ensure_uuid(data.block_id, field="blockId") if data.block_id else None
        if block_id is None:
            blocks_res = await db.execute(
                select(SessionBlock)
                .join(SessionBlockLink, SessionBlockLink.block_id == SessionBlock.id)
                .where(SessionBlockLink.session_id == session_id)
            )
            for block in blocks_res.scalars().all():
                start_date_local = data.starts_at.date()
                if block.start_date <= start_date_local <= block.end_date:
                    block_id = block.id
                    break

        # Manually created occurrences are marked auto_generated=False
        o = SessionOccurrence(
            session_id=s.id,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            auto_generated=False,
            block_id=block_id,
        )
        db.add(o)
        await db.flush()
        return OccurrenceOut(
            id=str(o.id),
            sessionId=str(o.session_id),
            startsAt=o.starts_at,
            endsAt=o.ends_at,
            cancelled=o.cancelled,
            cancellationReason=o.cancellation_reason,
            autoGenerated=o.auto_generated,
            blockId=str(o.block_id) if o.block_id else None,
            blockName=None,
        )

    @patch(
        "/occurrences/{occurrence_id:uuid}/cancel",
        status_code=HTTP_200_OK,
        summary="Cancel or reinstate occurrence",
        tags=["Admin: Occurrences"],
    )
    async def cancel_occurrence(
        self, db: AsyncSession, occurrence_id: uuid.UUID, data: OccurrenceCancel
    ) -> OccurrenceOut:
        """Cancel or reinstate an occurrence.

        When the cancellation state/reason changes, confirmed signups are notified.
        """
        o = await db.get(SessionOccurrence, occurrence_id)
        if not o:
            raise NotFoundException(detail="Occurrence not found")

        was_cancelled = bool(o.cancelled)
        prev_reason = o.cancellation_reason

        o.cancelled = bool(data.cancelled)
        o.cancellation_reason = data.cancellation_reason
        await db.flush()

        # Automatic caregiver notification on cancellation/reinstatement.
        if was_cancelled != o.cancelled or prev_reason != o.cancellation_reason:
            session_res = await db.execute(
                select(Session).options(selectinload(Session.session_location)).where(Session.id == o.session_id)
            )
            session = session_res.scalar_one_or_none()
            if session:
                queue = get_queue()
                if o.cancelled:
                    title = "Session cancelled"
                    message = o.cancellation_reason or "This session has been cancelled."
                else:
                    title = "Session update"
                    message = "This session is scheduled to run as normal."

                await _notify_confirmed_signups(
                    db=db,
                    queue=queue,
                    session=session,
                    update_title=title,
                    update_message=message,
                    affected_date=_fmt_local_datetime(o.starts_at) if o.starts_at else None,
                )

        return OccurrenceOut(
            id=str(o.id),
            sessionId=str(o.session_id),
            startsAt=o.starts_at,
            endsAt=o.ends_at,
            cancelled=o.cancelled,
            cancellationReason=o.cancellation_reason,
        )

    # ---------- Signups ----------

    @get(
        "/sessions/{session_id:uuid}/signups",
        status_code=HTTP_200_OK,
        summary="List session signups",
        tags=["Admin: Signups"],
    )
    async def list_session_signups(
        self, db: AsyncSession, session_id: uuid.UUID, status: str | None = None
    ) -> list[AdminSignupOut]:
        """List signups for a session.

        Optionally filter by `status`.
        """
        stmt = (
            select(Signup, CaregiverStaffView, ChildStaffView)
            .join(CaregiverStaffView, Signup.caregiver_id == CaregiverStaffView.id)
            .join(ChildStaffView, Signup.child_id == ChildStaffView.id)
            .where(Signup.session_id == session_id)
        )
        if status is not None:
            stmt = stmt.where(Signup.status == status)
        stmt = stmt.order_by(Signup.created_at.asc())
        res = await db.execute(stmt)
        out: list[AdminSignupOut] = []
        for su, caregiver, child in res.all():
            out.append(
                AdminSignupOut(
                    id=str(su.id),
                    status=su.status,
                    createdAt=su.created_at,
                    sessionId=str(su.session_id),
                    childId=str(su.child_id),
                    caregiverId=str(su.caregiver_id),
                    studentName=child.name,
                    guardianName=caregiver.name,
                    email=caregiver.email,
                    phone=caregiver.phone,
                    dateOfBirth=child.date_of_birth,
                )
            )
        return out

    @patch(
        "/signups/{signup_id:uuid}/status",
        status_code=HTTP_200_OK,
        summary="Update signup status",
        tags=["Admin: Signups"],
    )
    async def set_signup_status(
        self, db: AsyncSession, signup_id: uuid.UUID, data: SignupStatusUpdate
    ) -> AdminSignupOut:
        """Set the status of a signup.

        Status changes may trigger caregiver notifications (e.g. waitlist -> confirmed).
        """
        su = await db.get(Signup, signup_id)
        if not su:
            raise NotFoundException(detail="Signup not found")

        old_status = su.status
        su.status = data.status
        if data.status == "withdrawn":
            su.withdrawn_at = datetime.now(UTC)
        else:
            su.withdrawn_at = None

        await db.flush()

        if old_status != su.status:
            # Automatic caregiver notifications for status changes.
            session_res = await db.execute(
                select(Session).options(selectinload(Session.session_location)).where(Session.id == su.session_id)
            )
            session = session_res.scalar_one_or_none()
            caregiver_res = await db.execute(select(CaregiverStaffView).where(CaregiverStaffView.id == su.caregiver_id))
            caregiver = caregiver_res.scalar_one_or_none()

            child_res = await db.execute(select(ChildStaffView).where(ChildStaffView.id == su.child_id))
            child = child_res.scalar_one_or_none()
            if session and caregiver and child and caregiver.email and caregiver.name:
                queue = get_queue()
                if queue:
                    try:
                        # If a signup becomes confirmed, send the dedicated email and schedule term emails.
                        if su.status == "confirmed" and old_status != "confirmed":
                            first_occ_res = await db.execute(
                                select(SessionOccurrence)
                                .where(
                                    SessionOccurrence.session_id == session.id,
                                    SessionOccurrence.cancelled.is_(False),
                                )
                                .order_by(SessionOccurrence.starts_at.asc())
                                .limit(1)
                            )
                            first_occ = first_occ_res.scalar_one_or_none()
                            first_session_date = _fmt_local_datetime(first_occ.starts_at) if first_occ else None
                            calendar_url = f"{settings.public_base_url}/api/v1/session/{session.id}/calendar.ics"

                            loc = getattr(session, "session_location", None)
                            await queue.enqueue(
                                "send_waitlist_confirmed_task",
                                to_email=caregiver.email,
                                caregiver_name=caregiver.name,
                                child_name=child.name,
                                session_name=session.name,
                                session_venue=getattr(loc, "name", None),
                                session_address=getattr(loc, "address", None),
                                session_time=_format_time_range(
                                    session.day_of_week, session.start_time, session.end_time
                                ),
                                first_session_date=first_session_date,
                                calendar_url=calendar_url,
                                what_to_bring=session.what_to_bring,
                                contact_email=getattr(loc, "contact_email", None),
                            )
                        else:
                            # Generic status-change notification.
                            loc = getattr(session, "session_location", None)
                            await queue.enqueue(
                                "send_session_change_alert_task",
                                to_email=caregiver.email,
                                caregiver_name=caregiver.name,
                                child_name=child.name,
                                session_name=session.name,
                                session_venue=getattr(loc, "name", None),
                                session_address=getattr(loc, "address", None),
                                session_time=_format_time_range(
                                    session.day_of_week, session.start_time, session.end_time
                                ),
                                update_title="Signup status updated",
                                update_message=f"Your signup status changed from {old_status} to {su.status}.",
                                affected_date=None,
                                contact_email=getattr(loc, "contact_email", None),
                            )
                    except Exception as exc:  # best-effort notifications
                        logger.warning("Queue enqueue failed for signup %s: %s", su.id, exc)
                else:
                    logger.info("Queue not configured; skipping notifications for signup %s", su.id)

        return AdminSignupOut(
            id=str(su.id),
            status=su.status,
            createdAt=su.created_at,
            sessionId=str(su.session_id),
            childId=str(su.child_id),
            caregiverId=str(su.caregiver_id),
            studentName=(child.name if "child" in locals() and child else None),
            guardianName=(caregiver.name if "caregiver" in locals() and caregiver else None),
            email=(caregiver.email if "caregiver" in locals() and caregiver else None),
            phone=(caregiver.phone if "caregiver" in locals() and caregiver else None),
        )

    # ---------- Attendance ----------

    @get(
        "/occurrences/{occurrence_id:uuid}/roll",
        status_code=HTTP_200_OK,
        summary="Get attendance roll",
        tags=["Admin: Attendance"],
    )
    async def get_roll(self, db: AsyncSession, occurrence_id: uuid.UUID) -> AttendanceRollOut:
        """Return the attendance roll for an occurrence.

        Includes confirmed signups and any existing attendance records.
        """
        occ = await db.get(SessionOccurrence, occurrence_id)
        if not occ:
            raise NotFoundException(detail="Occurrence not found")
        if occ.cancelled:
            raise ValidationException(detail="Cannot take attendance for a cancelled occurrence")

        signups_res = await db.execute(
            select(Signup, ChildStaffView)
            .join(ChildStaffView, Signup.child_id == ChildStaffView.id)
            .where(Signup.session_id == occ.session_id, Signup.status == "confirmed")
            .order_by(Signup.created_at.asc())
        )
        rows = signups_res.all()

        attendance_res = await db.execute(select(AttendanceRecord).where(AttendanceRecord.occurrence_id == occ.id))
        attendance_by_child = {a.child_id: a for a in attendance_res.scalars().all()}

        occ_out = OccurrenceOut(
            id=str(occ.id),
            sessionId=str(occ.session_id),
            startsAt=occ.starts_at,
            endsAt=occ.ends_at,
            cancelled=occ.cancelled,
            cancellationReason=occ.cancellation_reason,
        )

        items: list[AttendanceRollItem] = []
        for su, child in rows:
            a = attendance_by_child.get(child.id)
            items.append(
                AttendanceRollItem(
                    childId=str(child.id),
                    childName=child.name,
                    signupId=str(su.id),
                    attendance=(
                        AttendanceRecordOut(
                            id=str(a.id),
                            occurrenceId=str(a.occurrence_id),
                            childId=str(a.child_id),
                            status=cast("AttendanceStatus", a.status),
                            reason=a.reason,
                        )
                        if a
                        else None
                    ),
                )
            )

        return AttendanceRollOut(occurrence=occ_out, items=items)

    @post(
        "/occurrences/{occurrence_id:uuid}/attendance",
        status_code=HTTP_200_OK,
        summary="Upsert attendance",
        tags=["Admin: Attendance"],
    )
    async def upsert_attendance(
        self, db: AsyncSession, occurrence_id: uuid.UUID, data: AttendanceUpsert
    ) -> AttendanceRecordOut:
        """Create or update an attendance record for a child.

        Also records an audit log entry with the actor/reason.
        """
        occ = await db.get(SessionOccurrence, occurrence_id)
        if not occ:
            raise NotFoundException(detail="Occurrence not found")
        if occ.cancelled:
            raise ValidationException(detail="Cannot take attendance for a cancelled occurrence")

        child_id = _ensure_uuid(data.child_id, field="childId")

        existing_res = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.occurrence_id == occurrence_id,
                AttendanceRecord.child_id == child_id,
            )
        )
        rec = existing_res.scalar_one_or_none()

        old_status = rec.status if rec else None
        old_reason = rec.reason if rec else None

        if not rec:
            rec = AttendanceRecord(
                occurrence_id=occurrence_id,
                child_id=child_id,
                status=data.status,
                reason=data.reason,
            )
            db.add(rec)
        else:
            rec.status = data.status
            rec.reason = data.reason

        db.add(
            AttendanceAuditLog(
                occurrence_id=occurrence_id,
                child_id=child_id,
                actor=data.actor,
                old_status=old_status,
                new_status=data.status,
                old_reason=old_reason,
                new_reason=data.reason,
            )
        )

        await db.flush()

        return AttendanceRecordOut(
            id=str(rec.id),
            occurrenceId=str(rec.occurrence_id),
            childId=str(rec.child_id),
            status=cast("AttendanceStatus", rec.status),
            reason=rec.reason,
        )

    @get(
        "/occurrences/{occurrence_id:uuid}/attendance-history",
        status_code=HTTP_200_OK,
        summary="Get attendance history",
        tags=["Admin: Attendance"],
    )
    async def get_attendance_history(
        self, db: AsyncSession, occurrence_id: uuid.UUID, child_id: uuid.UUID | None = None
    ) -> list[AttendanceRecordOut]:
        """Get attendance records for an occurrence, optionally filtered by child."""
        stmt = select(AttendanceRecord).where(AttendanceRecord.occurrence_id == occurrence_id)
        if child_id:
            stmt = stmt.where(AttendanceRecord.child_id == child_id)
        stmt = stmt.order_by(AttendanceRecord.id.desc())

        res = await db.execute(stmt)
        records = res.scalars().all()

        return [
            AttendanceRecordOut(
                id=str(r.id),
                occurrenceId=str(r.occurrence_id),
                childId=str(r.child_id),
                status=cast("AttendanceStatus", r.status),
                reason=r.reason,
            )
            for r in records
        ]

    # ---------- Child Notes ----------

    @get(
        "/children",
        status_code=HTTP_200_OK,
        summary="List children",
        tags=["Admin: Children"],
    )
    async def list_children(self, db: AsyncSession) -> list[ChildAdminOut]:
        """List all children with their details."""
        res = await db.execute(select(ChildStaffView).order_by(ChildStaffView.name.asc()))
        children = res.scalars().all()
        return [
            ChildAdminOut(
                id=str(c.id),
                caregiverId=str(c.caregiver_id),
                name=c.name,
                dateOfBirth=c.date_of_birth,
                mediaConsent=c.media_consent,
                medicalInfo=c.medical_info,
                otherInfo=c.other_info,
            )
            for c in children
        ]

    @get(
        "/children/{child_id:uuid}",
        status_code=HTTP_200_OK,
        summary="Get child",
        tags=["Admin: Children"],
    )
    async def get_child(self, db: AsyncSession, child_id: uuid.UUID) -> ChildAdminOut:
        """Get child details for admin use."""
        c_res = await db.execute(select(ChildStaffView).where(ChildStaffView.id == child_id))
        c = c_res.scalar_one_or_none()
        if not c:
            raise NotFoundException(detail="Child not found")
        return ChildAdminOut(
            id=str(c.id),
            caregiverId=str(c.caregiver_id),
            name=c.name,
            dateOfBirth=c.date_of_birth,
            mediaConsent=c.media_consent,
            medicalInfo=c.medical_info,
            otherInfo=c.other_info,
        )

    @get(
        "/children/{child_id:uuid}/notes",
        status_code=HTTP_200_OK,
        summary="List child notes",
        tags=["Admin: Children"],
    )
    async def list_child_notes(self, db: AsyncSession, child_id: uuid.UUID) -> list[ChildNoteOut]:
        """List internal notes for a child."""
        res = await db.execute(select(ChildNote).where(ChildNote.child_id == child_id))
        notes = res.scalars().all()
        return [
            ChildNoteOut(
                id=str(n.id),
                child_id=str(n.child_id),
                author=n.author,
                note=n.note,
            )
            for n in notes
        ]

    @post(
        "/children/{child_id:uuid}/notes",
        status_code=HTTP_200_OK,
        summary="Add child note",
        tags=["Admin: Children"],
    )
    async def add_child_note(self, db: AsyncSession, child_id: uuid.UUID, data: ChildNoteCreate) -> ChildNoteOut:
        """Add an internal note for a child."""
        exists_res = await db.execute(select(ChildStaffView.id).where(ChildStaffView.id == child_id))
        if exists_res.scalar_one_or_none() is None:
            raise NotFoundException(detail="Child not found")
        n = ChildNote(child_id=child_id, note=data.note, author=data.author)
        db.add(n)
        await db.flush()
        return ChildNoteOut(
            id=str(n.id),
            child_id=str(n.child_id),
            author=n.author,
            note=n.note,
        )

    # ---------- Communications ----------

    @post(
        "/sessions/{session_id:uuid}/email",
        status_code=HTTP_200_OK,
        summary="Send bulk email",
        tags=["Admin: Communications"],
    )
    async def bulk_email_session(self, db: AsyncSession, session_id: uuid.UUID, data: BulkEmailRequest) -> dict:
        """Send a custom email to all confirmed signups for a session."""
        session_res = await db.execute(
            select(Session).options(selectinload(Session.session_location)).where(Session.id == session_id)
        )
        session = session_res.scalar_one_or_none()
        if not session:
            raise NotFoundException(detail="Session not found")

        res = await db.execute(
            select(Signup, CaregiverStaffView, ChildStaffView)
            .join(CaregiverStaffView, Signup.caregiver_id == CaregiverStaffView.id)
            .join(ChildStaffView, Signup.child_id == ChildStaffView.id)
            .where(Signup.session_id == session_id, Signup.status == "confirmed")
            .order_by(Signup.created_at.asc())
        )
        rows = res.all()

        queue = get_queue()
        enqueued = 0
        for su, caregiver, child in rows:
            if not caregiver.email or not caregiver.name:
                continue
            await _enqueue_custom_bulk_email(
                queue=queue,
                to_email=caregiver.email,
                caregiver_name=caregiver.name,
                child_name=child.name,
                session=session,
                subject=data.subject,
                message=data.message,
            )
            enqueued += 1

        return {"enqueued": enqueued}

    @post(
        "/sessions/{session_id:uuid}/notify",
        status_code=HTTP_200_OK,
        summary="Notify confirmed signups",
        tags=["Admin: Communications"],
    )
    async def notify_session(self, db: AsyncSession, session_id: uuid.UUID, data: SessionChangeAlertRequest) -> dict:
        """Send a notification to all confirmed signups for a session.

        This reuses the existing `session_change_alert` email template.
        """
        session_res = await db.execute(
            select(Session).options(selectinload(Session.session_location)).where(Session.id == session_id)
        )
        session = session_res.scalar_one_or_none()
        if not session:
            raise NotFoundException(detail="Session not found")

        queue = get_queue()
        enqueued = await _notify_confirmed_signups(
            db=db,
            queue=queue,
            session=session,
            update_title=data.update_title,
            update_message=data.update_message,
            affected_date=data.affected_date,
        )
        return {"enqueued": enqueued}

    # ---------- Exports ----------

    @get(
        "/sessions/{session_id:uuid}/export/signups.csv",
        summary="Export signups CSV",
        tags=["Admin: Exports"],
    )
    async def export_signups_csv(self, db: AsyncSession, session_id: uuid.UUID, status: str | None = None) -> Response:
        """Export signups for a session as a CSV file."""
        stmt = (
            select(Signup, CaregiverStaffView, ChildStaffView)
            .join(CaregiverStaffView, Signup.caregiver_id == CaregiverStaffView.id)
            .join(ChildStaffView, Signup.child_id == ChildStaffView.id)
            .where(Signup.session_id == session_id)
        )
        if status is not None:
            stmt = stmt.where(Signup.status == status)
        stmt = stmt.order_by(Signup.created_at.asc())
        res = await db.execute(stmt)
        rows = res.all()

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "signup_id",
                "status",
                "created_at",
                "child_name",
                "guardian_name",
                "email",
                "phone",
            ]
        )
        for su, caregiver, child in rows:
            w.writerow(
                [
                    str(su.id),
                    su.status,
                    su.created_at.isoformat(),
                    child.name or "",
                    caregiver.name or "",
                    caregiver.email or "",
                    caregiver.phone or "",
                ]
            )

        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=signups-{session_id}.csv"},
        )

    @get(
        "/sessions/{session_id:uuid}/export/attendance.csv",
        summary="Export attendance CSV",
        tags=["Admin: Exports"],
    )
    async def export_attendance_csv(self, db: AsyncSession, session_id: uuid.UUID) -> Response:
        """Export attendance for a session as a CSV file."""
        occ_res = await db.execute(
            select(SessionOccurrence)
            .where(SessionOccurrence.session_id == session_id)
            .order_by(SessionOccurrence.starts_at.asc())
        )
        occurrences = occ_res.scalars().all()
        occ_ids = [o.id for o in occurrences]

        att_res = await db.execute(select(AttendanceRecord).where(AttendanceRecord.occurrence_id.in_(occ_ids)))
        attendance = att_res.scalars().all()

        child_ids = {a.child_id for a in attendance}
        if child_ids:
            child_res = await db.execute(select(ChildStaffView).where(ChildStaffView.id.in_(child_ids)))
            children = {c.id: c for c in child_res.scalars().all()}
        else:
            children = {}

        occ_by_id = {o.id: o for o in occurrences}

        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(
            [
                "occurrence_id",
                "occurrence_start",
                "child_id",
                "child_name",
                "status",
                "reason",
            ]
        )
        for a in attendance:
            child = children.get(a.child_id)
            occ = occ_by_id.get(a.occurrence_id)
            w.writerow(
                [
                    str(a.occurrence_id),
                    (occ.starts_at.isoformat() if occ else ""),
                    str(a.child_id),
                    child.name if child else "",
                    a.status,
                    a.reason or "",
                ]
            )

        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=attendance-{session_id}.csv"},
        )

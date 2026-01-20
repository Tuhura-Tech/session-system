from __future__ import annotations

from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

_DOW_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _format_time_range(day_of_week: int | None, start_time: time | None, end_time: time | None) -> str:
    if day_of_week is None:
        dow = ""
    else:
        dow = _DOW_SHORT[int(day_of_week)] if 0 <= int(day_of_week) <= 6 else ""

    def fmt(t) -> str:
        # 12-hour formatting without leading 0.
        hour = t.hour
        minute = t.minute
        ampm = "am" if hour < 12 else "pm"
        hour12 = hour % 12
        if hour12 == 0:
            hour12 = 12
        if minute:
            return f"{hour12}:{minute:02d}{ampm}"
        return f"{hour12}{ampm}"

    if not start_time or not end_time:
        return dow
    return f"{dow} {fmt(start_time)}–{fmt(end_time)}".strip()


class LatLng(BaseModel):
    """Latitude and longitude pair."""

    model_config = ConfigDict(from_attributes=True)

    lat: float
    lng: float


class SessionPublic(BaseModel):
    """Public session information (safe to show caregivers)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    age: str
    time: str
    term_summary: str | None = None
    blocks: list[str] = []  # Block names/types this session runs in
    public_instructions: str | None = None
    arrival_instructions: str | None = None
    what_to_bring: str | None = None
    prerequisites: str | None = None
    waitlist: bool = False

    location_details: SessionLocationDetails | None = Field(None, alias="locationDetails")

    @classmethod
    def from_orm_model(cls, session, blocks: list[str] | None = None) -> SessionPublic:
        """Convert ORM model to schema.

        Args:
            session: Session ORM model or sessions_public view row
            blocks: Optional list of block names. If not provided, will attempt to extract from session.block_links
        """
        # Support both:
        # - Session ORM model with session_location relationship
        # - sessions_public DB view row with flattened location_* columns
        loc = getattr(session, "session_location", None)

        location_details = None
        if loc is not None:
            location_details = SessionLocationDetails(
                id=str(loc.id),
                name=loc.name,
                address=loc.address,
                region=loc.region,
                latlong=LatLng(lat=loc.lat, lng=loc.lng),
            )
        else:
            location_id = getattr(session, "location_id", None)
            if location_id is not None:
                location_details = SessionLocationDetails(
                    id=str(location_id),
                    name=getattr(session, "location_name", ""),
                    address=getattr(session, "location_address", ""),
                    region=getattr(session, "location_region", ""),
                    latlong=LatLng(
                        lat=float(getattr(session, "location_lat", 0) or 0),
                        lng=float(getattr(session, "location_lng", 0) or 0),
                    ),
                )

        age = f"Years {session.age_lower}-{session.age_upper}"
        time_str = _format_time_range(session.day_of_week, session.start_time, session.end_time)

        # Until venue guidance is split into multiple fields, re-use location.instructions.
        if loc is not None:
            instructions = getattr(loc, "instructions", None)
        else:
            instructions = getattr(session, "location_instructions", None)

        # Sessions are not attached to a single term; for term sessions show the year.
        session_type = getattr(session, "session_type", None)
        term_name = f"{getattr(session, 'year', '')}" if session_type == "term" else None

        # Extract block information if not provided
        if blocks is None:
            blocks = []
            block_links = getattr(session, "block_links", None)
            if block_links:
                # Sort blocks by type order: term_1, term_2, term_3, term_4, special
                block_order = {
                    "term_1": 0,
                    "term_2": 1,
                    "term_3": 2,
                    "term_4": 3,
                    "special": 4,
                }
                sorted_links = sorted(
                    block_links,
                    key=lambda bl: block_order.get(getattr(bl.block, "block_type", ""), 99),
                )
                blocks = [bl.block.name for bl in sorted_links if bl.block]

        return cls(
            id=str(session.id),
            name=session.name,
            age=age,
            time=time_str,
            term_summary=term_name,
            blocks=blocks,
            public_instructions=instructions,
            arrival_instructions=instructions,
            what_to_bring=session.what_to_bring,
            prerequisites=session.prerequisites,
            waitlist=session.waitlist,
            locationDetails=location_details,
        )

        # Sessions are not attached to a single term; for term sessions show the year.
        session_type = getattr(session, "session_type", None)
        term_name = f"{getattr(session, 'year', '')}" if session_type == "term" else None

        return cls(
            id=str(session.id),
            name=session.name,
            age=age,
            time=time_str,
            term_summary=term_name,
            public_instructions=instructions,
            arrival_instructions=instructions,
            what_to_bring=session.what_to_bring,
            prerequisites=session.prerequisites,
            waitlist=session.waitlist,
            locationDetails=location_details,
        )


class SessionOccurrencePublic(BaseModel):
    """A single scheduled occurrence of a session."""

    model_config = ConfigDict(from_attributes=True)

    starts_at: datetime
    ends_at: datetime
    cancelled: bool = False
    cancellation_reason: str | None = None


class BlockOccurrences(BaseModel):
    """Occurrences grouped by block."""

    block_id: str
    block_name: str
    block_type: str
    occurrences: list[SessionOccurrencePublic] = []


class SessionPublicDetail(SessionPublic):
    """Public session details including scheduled occurrences grouped by block."""

    occurrences_by_block: list[BlockOccurrences] = []

    @classmethod
    def from_orm_model(
        cls,
        session,
        blocks: list[str] | None = None,
        occurrences_by_block: list[BlockOccurrences] | None = None,
    ) -> SessionPublicDetail:
        base = SessionPublic.from_orm_model(session, blocks=blocks)

        return cls(
            **base.model_dump(by_alias=True),
            occurrences_by_block=occurrences_by_block or [],
        )


class SessionLocationDetails(BaseModel):
    """Physical venue/location details for a session."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    address: str
    region: str
    latlong: LatLng


class SessionRegionGroup(BaseModel):
    """Sessions grouped by region for discovery screens."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    sessions: list[SessionPublic]

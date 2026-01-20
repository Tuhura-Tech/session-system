from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.view_base import ViewBase


class SessionPublicView(ViewBase):
    """Read-only projection of sessions safe for public/caregiver browsing.

    This view intentionally omits staff-only fields (e.g. internal_notes, photo_album_url)
    and any other columns that must never be loaded for public endpoints.
    """

    __tablename__ = "sessions_public"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True)

    name: Mapped[str] = mapped_column(String(255))

    age_lower: Mapped[int] = mapped_column(Integer)
    age_upper: Mapped[int] = mapped_column(Integer)

    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    year: Mapped[int] = mapped_column(Integer)
    session_type: Mapped[str] = mapped_column(String(10))

    what_to_bring: Mapped[str | None] = mapped_column(String, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(String, nullable=True)

    waitlist: Mapped[bool] = mapped_column(Boolean, default=False)

    location_id: Mapped[uuid.UUID] = mapped_column(UUID())
    location_name: Mapped[str] = mapped_column(String(255))
    location_address: Mapped[str] = mapped_column(String(500))
    location_region: Mapped[str] = mapped_column(String(100))
    location_lat: Mapped[float] = mapped_column(Float)
    location_lng: Mapped[float] = mapped_column(Float)
    location_instructions: Mapped[str | None] = mapped_column(String(500), nullable=True)


class SessionOccurrencePublicView(ViewBase):
    """Read-only projection of session occurrences safe for public output."""

    __tablename__ = "session_occurrences_public"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(), index=True)

    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)


class ChildStaffView(ViewBase):
    """Read-only projection of children safe for staff/admin.

    Demographic reporting fields (region, ethnicity, school_name) are intentionally omitted.
    """

    __tablename__ = "children_staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True)
    caregiver_id: Mapped[uuid.UUID] = mapped_column(UUID(), index=True)

    name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[date] = mapped_column(Date)

    media_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    medical_info: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    needs_devices: Mapped[bool] = mapped_column(Boolean, default=False)
    other_info: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class CaregiverStaffView(ViewBase):
    """Read-only projection of caregivers safe for staff/admin."""

    __tablename__ = "caregivers_staff"

    id: Mapped[uuid.UUID] = mapped_column(UUID(), primary_key=True)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

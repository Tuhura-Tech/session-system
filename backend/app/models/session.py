from __future__ import annotations

import enum
import uuid
from datetime import time
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, Text, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey
from app.models.types import IntEnumType

if TYPE_CHECKING:
    from app.models.session_block_link import SessionBlockLink
    from app.models.session_occurrence import SessionOccurrence
    from app.models.session_staff import SessionStaff
    from app.models.signup import Signup


class DayOfWeekEnum(enum.IntEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class Session(Base, UUIDPrimaryKey, TimestampMixin):
    """A session definition.

    Session types:
    - term: a year-long weekly session (runs during school terms).
    - special: a one-off program with a custom set of occurrences.
    """

    __tablename__ = "sessions"

    __table_args__ = (
        CheckConstraint("session_type IN ('term','special')", name="ck_sessions_type"),
        CheckConstraint(
            "day_of_week IS NULL OR day_of_week BETWEEN 0 AND 6",
            name="ck_sessions_day_of_week_nullable",
        ),
        CheckConstraint(
            "(session_type = 'term' AND day_of_week IS NOT NULL) OR (session_type = 'special')",
            name="ck_sessions_term_requires_schedule",
        ),
    )

    session_location_id: Mapped[uuid.UUID] = mapped_column(UUID(), ForeignKey("session_locations.id"), nullable=False)

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    session_type: Mapped[str] = mapped_column(String(10), nullable=False, default="term", index=True)

    # Core fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Age details
    age_lower: Mapped[int] = mapped_column(Integer, nullable=False)
    age_upper: Mapped[int] = mapped_column(Integer, nullable=False)

    # Day of week (0=Mon .. 6=Sun)
    day_of_week: Mapped[DayOfWeekEnum | None] = mapped_column(IntEnumType(DayOfWeekEnum), nullable=True)

    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Capacity
    waitlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Public venue info
    what_to_bring: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Staff-only (not exposed in public endpoints)
    photo_album_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Relationships
    session_location = relationship("SessionLocation", back_populates="sessions")
    signups: Mapped[list[Signup]] = relationship("Signup", back_populates="session", lazy="selectin")

    occurrences: Mapped[list[SessionOccurrence]] = relationship(
        "SessionOccurrence",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    block_links: Mapped[list[SessionBlockLink]] = relationship(
        "SessionBlockLink",
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    session_staff_assignments: Mapped[list[SessionStaff]] = relationship(
        "SessionStaff",
        back_populates="session",
        cascade="all, delete-orphan",
    )

    @property
    def blocks(self) -> list:
        """Get all blocks this session runs in, ordered by date."""
        from app.models.session_block import SessionBlock

        blocks: list[SessionBlock] = [link.block for link in self.block_links]
        return sorted(blocks, key=lambda b: (b.year, b.block_type.value))

    @property
    def occurrences_by_block(self) -> dict:
        """Get occurrences organized by block."""
        result = {}
        for occurrence in self.occurrences:
            if occurrence.block_id:
                if occurrence.block_id not in result:
                    result[occurrence.block_id] = []
                result[occurrence.block_id].append(occurrence)
        return result

    def confirmed_count(self) -> int:
        """Count confirmed signups."""
        return sum(1 for s in self.signups if s.status == "confirmed")

    def capacity_left(self) -> int:
        """Get the remaining capacity."""
        return max(0, self.capacity - self.confirmed_count())

    def is_at_capacity(self) -> bool:
        """Check if session has reached capacity."""
        return self.confirmed_count() >= self.capacity

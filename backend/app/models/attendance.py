from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Literal

from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKey

if TYPE_CHECKING:
    from app.models.child import Child
    from app.models.session_occurrence import SessionOccurrence


AttendanceStatus = Literal["present", "absent_known", "absent_unknown"]


class AttendanceRecord(Base, UUIDPrimaryKey):
    """Attendance for a child at a particular session occurrence."""

    __tablename__ = "attendance_records"
    __table_args__ = (
        CheckConstraint(
            "status IN ('present','absent_known','absent_unknown')",
            name="ck_attendance_records_status",
        ),
    )

    occurrence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("session_occurrences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    occurrence: Mapped[SessionOccurrence] = relationship("SessionOccurrence", lazy="selectin")
    child: Mapped[Child] = relationship("Child", lazy="selectin")

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class AttendanceAuditLog(Base, UUIDPrimaryKey):
    """Audit log for attendance changes (who/when/what changed).

    Auth is deferred; `actor` may be provided by the caller.
    """

    __tablename__ = "attendance_audit_logs"

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

    actor: Mapped[str | None] = mapped_column(String(255), nullable=True)

    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(20), nullable=True)

    old_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

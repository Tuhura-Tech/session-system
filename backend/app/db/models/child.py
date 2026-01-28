from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from advanced_alchemy.base import UUIDv7AuditBase

if TYPE_CHECKING:
    from app.db.models.caregiver import Caregiver
    from app.db.models.signup import Signup


class Child(UUIDv7AuditBase):
    """Child records derived from signups for operational continuity."""

    __tablename__ = "children"

    caregiver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(), ForeignKey("caregivers.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)

    media_consent: Mapped[bool] = mapped_column(nullable=False, default=False)
    medical_info: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    needs_devices: Mapped[bool] = mapped_column(nullable=False, default=False)
    other_info: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Demographic information for reporting (NEVER exposed to staff)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ethnicity: Mapped[str | None] = mapped_column(String(200), nullable=True)
    school_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    caregiver: Mapped[Caregiver] = relationship("Caregiver", back_populates="children")
    signups: Mapped[list[Signup]] = relationship("Signup", back_populates="child")

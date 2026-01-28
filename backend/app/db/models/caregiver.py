from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from advanced_alchemy.base import UUIDv7AuditBase

if TYPE_CHECKING:
    from app.db.models.child import Child
    from app.db.models.signup import Signup


class Caregiver(UUIDv7AuditBase):
    """Caregiver account authenticated via magic link (passwordless)."""

    __tablename__ = "caregivers"

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    referral_source: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    children: Mapped[list[Child]] = relationship(
        "Child", back_populates="caregiver", lazy="selectin"
    )
    signups: Mapped[list[Signup]] = relationship(
        "Signup", back_populates="caregiver", lazy="selectin"
    )

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from advanced_alchemy.base import UUIDv7AuditBase

if TYPE_CHECKING:
    from app.db.models.session import Session
    from app.db.models.session_block import SessionBlock


class SessionBlockLink(UUIDv7AuditBase):
    """Links a session to a block it runs in.

    When a session is registered in a block, the registration carries over all
    blocks the session is linked to. This simplifies signup management.

    Example:
    - Admin creates session "Gymnastics" running in Terms 1, 2, and 3
    - Creates three SessionBlockLink entries
    - When caregiver registers, registration automatically covers all three blocks
    """

    __tablename__ = "session_block_links"

    __table_args__ = (
        UniqueConstraint(
            "session_id", "block_id", name="uq_session_block_links_session_block"
        ),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    block_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("session_blocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    session: Mapped[Session] = relationship("Session", back_populates="block_links")
    block: Mapped[SessionBlock] = relationship(
        "SessionBlock", back_populates="session_block_links"
    )

    def __repr__(self) -> str:
        return (
            f"SessionBlockLink(session_id={self.session_id}, block_id={self.block_id})"
        )

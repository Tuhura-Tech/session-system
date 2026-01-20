from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKey


class ChildNote(Base, UUIDPrimaryKey):
    """Staff/admin note on a child (author + timestamp)."""

    __tablename__ = "child_notes"

    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(),
        ForeignKey("children.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)

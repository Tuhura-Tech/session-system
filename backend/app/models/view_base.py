from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class ViewBase(DeclarativeBase):
    """Declarative base for read-only DB views.

    Kept separate from the main model Base so `Base.metadata.create_all()`
    (used in dev and in SQLite tests) does not create physical tables for views.
    """

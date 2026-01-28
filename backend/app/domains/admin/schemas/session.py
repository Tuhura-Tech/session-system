from __future__ import annotations
from saq.worker import start

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Session(CamelizedBaseSchema):
    id: UUID
    year: int
    session_type: Literal["term", "special"]
    name: str
    age_lower: int
    age_upper: int

    start_time: time
    end_time: time

    waitlist: bool
    capacity: int

    what_to_bring: str | None = None
    prerequisites: str | None = None

    photo_album_url: str | None = None
    internal_notes: str | None = None

    archived: bool


class SessionCreate(CamelizedBaseSchema):
    year: int
    session_type: Literal["term", "special"]
    name: str
    age_lower: int
    age_upper: int

    start_time: time
    end_time: time

    waitlist: bool
    capacity: int

    what_to_bring: str | None = None
    prerequisites: str | None = None

    photo_album_url: str | None = None
    internal_notes: str | None = None

    archived: bool = False


class SessionUpdate(CamelizedBaseSchema):
    year: int | None = None
    session_type: Literal["term", "special"] | None = None
    name: str | None = None
    age_lower: int | None = None
    age_upper: int | None = None

    start_time: time | None = None
    end_time: time | None = None

    waitlist: bool | None = None
    capacity: int | None = None

    what_to_bring: str | None = None
    prerequisites: str | None = None

    photo_album_url: str | None = None
    internal_notes: str | None = None

    archived: bool | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.year,
                values.session_type,
                values.name,
                values.age_lower,
                values.age_upper,
                values.start_time,
                values.end_time,
                values.waitlist,
                values.capacity,
                values.what_to_bring,
                values.prerequisites,
                values.photo_album_url,
                values.internal_notes,
                values.archived,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

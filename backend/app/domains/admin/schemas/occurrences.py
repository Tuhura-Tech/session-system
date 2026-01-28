from __future__ import annotations
from saq.worker import start

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Occurrence(CamelizedBaseSchema):
    id: UUID
    
    starts_at: datetime
    ends_at: datetime

    cancelled: bool
    cancellation_reason: str | None = None


class OccurrenceCreate(CamelizedBaseSchema):
    starts_at: datetime
    ends_at: datetime

    cancelled: bool = False
    cancellation_reason: str | None = None


class OccurrenceUpdate(CamelizedBaseSchema):
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    cancelled: bool | None = None
    cancellation_reason: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.starts_at,
                values.ends_at,
                values.cancelled,
                values.cancellation_reason,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

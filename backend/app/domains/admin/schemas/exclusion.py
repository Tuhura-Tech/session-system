from __future__ import annotations
from saq.worker import start

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class ExclusionDate(CamelizedBaseSchema):
    id: UUID
    year: int
    exclusion_date: date
    reason: str | None = None


class ExclusionDateCreate(CamelizedBaseSchema):
    year: int
    exclusion_date: date
    reason: str | None = None


class ExclusionDateUpdate(CamelizedBaseSchema):
    year: int | None = None
    exclusion_date: date | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.year,
                values.exclusion_date,
                values.reason,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

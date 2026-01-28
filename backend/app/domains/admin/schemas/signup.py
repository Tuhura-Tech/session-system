from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Signup(CamelizedBaseSchema):
    id: UUID
    status: str
    withdrawn_at: datetime | None = None

    pickup_dropoff: str | None = None

class SignupCreate(CamelizedBaseSchema):
    status: str
    withdrawn_at: datetime | None = None
    pickup_dropoff: str | None = None


class SignupUpdate(CamelizedBaseSchema):
    status: str | None = None
    withdrawn_at: datetime | None = None
    pickup_dropoff: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.status,
                values.withdrawn_at,
                values.pickup_dropoff,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

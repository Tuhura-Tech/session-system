from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Block(CamelizedBaseSchema):
    id: UUID
    year: int
    block_type: str
    name: str
    start_date: date
    end_date: date


class BlockCreate(CamelizedBaseSchema):
    year: int
    block_type: str
    name: str
    start_date: date
    end_date: date


class BlockUpdate(CamelizedBaseSchema):
    year: int | None = None
    block_type: str | None = None
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.year,
                values.block_type,
                values.name,
                values.start_date,
                values.end_date,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

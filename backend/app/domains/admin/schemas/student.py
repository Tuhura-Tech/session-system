from __future__ import annotations
from saq.worker import start

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Student(CamelizedBaseSchema):
    id: UUID
    name: str
    date_of_birth: date

    media_consent: bool
    medical_info: str | None = None
    needs_devices: bool
    other_info: str | None = None


class StudentCreate(CamelizedBaseSchema):
    name: str
    date_of_birth: date

    media_consent: bool
    medical_info: str | None = None
    needs_devices: bool
    other_info: str | None = None

    region: str | None = None
    ethnicity: str | None = None
    school_name: str | None = None
    gender: str | None = None


class StudentUpdate(CamelizedBaseSchema):
    name: str | None = None
    date_of_birth: date | None = None
    media_consent: bool | None = None
    medical_info: str | None = None
    needs_devices: bool | None = None
    other_info: str | None = None


    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.name,
                values.date_of_birth,
                values.media_consent,
                values.medical_info,
                values.needs_devices,
                values.other_info,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

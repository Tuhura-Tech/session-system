from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class RegionEnum(Enum):
    NORTHLAND: str = "Northland"
    AUCKLAND: str = "Auckland"
    WAIKATO: str = "Waikato"
    BAY_OF_PLENTY: str = "Bay of Plenty"
    GISBORNE: str = "Gisborne"
    HAWKES_BAY: str = "Hawkes Bay"
    TARANAKI: str = "Taranaki"
    MANAWATU_WANGANUI: str = "Manawatu-Wanganui"
    WELLINGTON: str = "Wellington"
    TASMAN: str = "Tasman"
    NELSON: str = "Nelson"
    MARLBOROUGH: str = "Marlborough"
    WEST_COAST: str = "West Coast"
    CANTERBURY: str = "Canterbury"
    OTAGO: str = "Otago"
    SOUTHLAND: str = "Southland"


class Location(CamelizedBaseSchema):
    id: UUID
    name: str
    address: str
    region: RegionEnum
    lat: float
    lng: float
    instructions: str | None = None

    contact_name: str = Field(..., alias="contactName")
    contact_email: EmailStr = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(None, alias="contactPhone")
    internal_notes: str | None = Field(None, alias="internalNotes")


class LocationCreate(CamelizedBaseSchema):
    name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    region: RegionEnum = Field(..., min_length=1)
    lat: float = Field(...)
    lng: float = Field(...)
    instructions: str | None = None

    contact_name: str = Field(..., alias="contactName", min_length=1)
    contact_email: EmailStr = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(None, alias="contactPhone")
    internal_notes: str | None = Field(None, alias="internalNotes")


class LocationUpdate(CamelizedBaseSchema):
    name: str | None = None
    address: str | None = None
    region: RegionEnum | None = None
    lat: float | None = None
    lng: float | None = None
    instructions: str | None = None

    contact_name: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = None
    internal_notes: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(cls, values):
        if all(
            v is None
            for v in [
                values.name,
                values.address,
                values.region,
                values.lat,
                values.lng,
                values.instructions,
                values.contact_name,
                values.contact_email,
                values.contact_phone,
                values.internal_notes,
            ]
        ):
            raise ValueError("At least one field must be provided for update.")
        return values

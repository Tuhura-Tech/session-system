from __future__ import annotations
from saq.worker import start

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from uuid import UUID

from app.lib.schema import CamelizedBaseSchema

from enum import Enum


class Staff(CamelizedBaseSchema):
    id: UUID
    name: str
    email: EmailStr

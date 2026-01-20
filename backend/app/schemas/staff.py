from __future__ import annotations

from datetime import datetime
from uuid import UUID

from litestar.plugins.pydantic import PydanticDTO
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StaffBase(BaseModel):
    """Base staff fields."""

    name: str = Field(..., max_length=255, description="Staff member's full name")
    email: EmailStr = Field(..., description="Staff member's email address")


class StaffCreate(StaffBase):
    """Schema for creating a staff member (from SSO)."""

    sso_id: str = Field(..., max_length=255, description="SSO identifier (e.g., sub claim)")


class StaffUpdate(BaseModel):
    """Schema for updating staff member details."""

    name: str | None = Field(None, max_length=255)
    email: EmailStr | None = None
    active: bool | None = None


class StaffResponse(StaffBase):
    """Staff response schema."""

    id: UUID
    sso_id: str
    active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StaffListItem(BaseModel):
    """Simplified staff info for lists."""

    id: UUID
    name: str
    email: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class SessionStaffAssignment(BaseModel):
    """Schema for assigning staff to a session."""

    staff_ids: list[UUID] = Field(..., description="List of staff member IDs to assign")


class SessionWithStaff(BaseModel):
    """Session info with assigned staff."""

    session_id: UUID
    staff: list[StaffListItem]

    model_config = ConfigDict(from_attributes=True)


# DTOs for Litestar
class StaffDTO(PydanticDTO[StaffResponse]):
    """DTO for staff responses."""


class StaffCreateDTO(PydanticDTO[StaffCreate]):
    """DTO for creating staff."""


class StaffUpdateDTO(PydanticDTO[StaffUpdate]):
    """DTO for updating staff."""

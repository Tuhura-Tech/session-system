from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SignupStatus = Literal["pending", "confirmed", "waitlisted", "withdrawn"]


class SignupCreateRequest(BaseModel):
    """Request body for creating a signup.

    This project uses authenticated caregiver signups. The only per-signup
    mutable field is pickup/dropoff notes; caregiver/child details live on the
    Caregiver/Child models.
    """

    model_config = ConfigDict(from_attributes=True)

    child_id: str = Field(..., alias="childId")
    pickup_dropoff: str | None = Field(None, alias="pickupDropoff")


class SignupCreateResponse(BaseModel):
    """Response after creating a signup."""

    id: str
    status: SignupStatus

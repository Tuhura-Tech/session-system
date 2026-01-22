from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class CaregiverMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str | None = None
    phone: str | None = None
    email_verified: bool = False
    profile_complete: bool = False  # True if name and phone are set


class CaregiverUpdate(BaseModel):
    name: str | None = Field(None, min_length=0)
    phone: str | None = Field(None, min_length=0)
    subscribe_newsletter: bool = Field(False, alias="subscribeNewsletter")
    referral_source: str | None = Field(None, alias="referralSource")


class ChildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    date_of_birth: date | None = Field(None, alias="dateOfBirth")
    media_consent: bool = Field(False, alias="mediaConsent")
    medical_info: str | None = Field(None, alias="medicalInfo")
    needs_devices: bool = Field(False, alias="needsDevices")
    other_info: str | None = Field(None, alias="otherInfo")

    # Demographic information (for reporting only, not exposed to staff)
    region: str | None = None
    ethnicity: str | None = None
    school_name: str | None = Field(None, alias="schoolName")


class ChildCreate(BaseModel):
    name: str = Field(..., min_length=1)
    date_of_birth: date = Field(..., alias="dateOfBirth")
    media_consent: bool = Field(False, alias="mediaConsent")
    medical_info: str | None = Field(None, alias="medicalInfo")
    needs_devices: bool = Field(False, alias="needsDevices")
    other_info: str | None = Field(None, alias="otherInfo")

    # Optional demographic information for reporting
    region: str | None = None
    ethnicity: str | None = None
    school_name: str | None = Field(None, alias="schoolName")
    gender: str | None = None


class ChildUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    date_of_birth: date | None = Field(None, alias="dateOfBirth")
    media_consent: bool | None = Field(None, alias="mediaConsent")
    medical_info: str | None = Field(None, alias="medicalInfo")
    needs_devices: bool | None = Field(None, alias="needsDevices")
    other_info: str | None = Field(None, alias="otherInfo")

    # Optional demographic information for reporting
    region: str | None = None
    ethnicity: str | None = None
    school_name: str | None = Field(None, alias="schoolName")
    gender: str | None = None

class AuthenticatedSignupCreate(BaseModel):
    child_id: str = Field(..., alias="childId")

    pickup_dropoff: str | None = Field(None, alias="pickupDropoff")
    pairing_preference: str | None = Field(None, alias="pairingPreference")


class CaregiverSignupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    created_at: datetime = Field(..., alias="createdAt")
    session_id: str = Field(..., alias="sessionId")
    session_name: str = Field(..., alias="sessionName")
    child_id: str = Field(..., alias="childId")
    child_name: str = Field(..., alias="childName")

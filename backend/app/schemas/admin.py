from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ---------- Blocks & Exclusions ----------


BlockType = Literal["term_1", "term_2", "term_3", "term_4", "special"]


class SessionBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    year: int
    block_type: BlockType = Field(..., alias="blockType")

    name: str
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    timezone: str


class SessionBlockCreate(BaseModel):
    year: int
    block_type: BlockType = Field(..., alias="blockType")

    name: str = Field(..., min_length=1)
    start_date: date = Field(..., alias="startDate")
    end_date: date = Field(..., alias="endDate")
    timezone: str = Field("Pacific/Auckland", min_length=1)


class SessionBlockUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    start_date: date | None = Field(None, alias="startDate")
    end_date: date | None = Field(None, alias="endDate")
    timezone: str | None = None


class ExclusionDateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    year: int
    date: date
    reason: str | None = None


class ExclusionDateCreate(BaseModel):
    date: date
    reason: str | None = None


class ExclusionDateUpdate(BaseModel):
    reason: str | None = None


# ---------- Locations & Sessions ----------


class SessionLocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    address: str
    region: str
    lat: float
    lng: float
    instructions: str | None = None

    contact_name: str = Field(..., alias="contactName")
    contact_email: EmailStr = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(None, alias="contactPhone")
    internal_notes: str | None = Field(None, alias="internalNotes")


class SessionLocationCreate(BaseModel):
    name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    region: str = Field(..., min_length=1)
    lat: float
    lng: float
    instructions: str | None = None

    contact_name: str = Field(..., alias="contactName", min_length=1)
    contact_email: EmailStr = Field(..., alias="contactEmail")
    contact_phone: str | None = Field(None, alias="contactPhone")
    internal_notes: str | None = Field(None, alias="internalNotes")


class SessionLocationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    address: str | None = Field(None, min_length=1)
    region: str | None = Field(None, min_length=1)
    lat: float | None = None
    lng: float | None = None
    instructions: str | None = None

    contact_name: str | None = Field(None, alias="contactName")
    contact_email: EmailStr | None = Field(None, alias="contactEmail")
    contact_phone: str | None = Field(None, alias="contactPhone")
    internal_notes: str | None = Field(None, alias="internalNotes")


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_location_id: str = Field(..., alias="sessionLocationId")
    session_type: str = Field(default="term", alias="sessionType")
    year: int

    name: str
    age_lower: int = Field(..., alias="ageLower")
    age_upper: int = Field(..., alias="ageUpper")

    day_of_week: int | None = Field(None, alias="dayOfWeek")
    start_time: time = Field(..., alias="startTime")
    end_time: time = Field(..., alias="endTime")

    waitlist: bool
    capacity: int

    what_to_bring: str | None = Field(None, alias="whatToBring")
    prerequisites: str | None = None

    photo_album_url: str | None = Field(None, alias="photoAlbumUrl")
    internal_notes: str | None = Field(None, alias="internalNotes")
    archived: bool

    # Block associations (for term-type sessions)
    block_ids: list[str] = Field(default_factory=list, alias="blockIds")


class SessionCreate(BaseModel):
    session_location_id: str = Field(..., alias="sessionLocationId")
    year: int

    name: str = Field(..., min_length=1)
    age_lower: int = Field(..., ge=0, alias="ageLower")
    age_upper: int = Field(..., ge=0, alias="ageUpper")

    day_of_week: int | None = Field(None, ge=0, le=6, alias="dayOfWeek")
    start_time: time = Field(..., alias="startTime")
    end_time: time = Field(..., alias="endTime")

    waitlist: bool = False
    capacity: int = Field(..., ge=0)
    session_type: str = Field(default="term", alias="sessionType")

    what_to_bring: str | None = Field(None, alias="whatToBring")
    prerequisites: str | None = None

    photo_album_url: str | None = Field(None, alias="photoAlbumUrl")
    internal_notes: str | None = Field(None, alias="internalNotes")
    archived: bool = False

    # Block associations (for term-type sessions)
    block_ids: list[str] = Field(default_factory=list, alias="blockIds")


class SessionUpdate(BaseModel):
    session_location_id: str | None = Field(None, alias="sessionLocationId")
    year: int | None = None

    name: str | None = Field(None, min_length=1)
    age_lower: int | None = Field(None, ge=0, alias="ageLower")
    age_upper: int | None = Field(None, ge=0, alias="ageUpper")

    day_of_week: int | None = Field(None, ge=0, le=6, alias="dayOfWeek")
    start_time: time | None = Field(None, alias="startTime")
    end_time: time | None = Field(None, alias="endTime")

    waitlist: bool | None = None
    capacity: int | None = Field(None, ge=0)
    session_type: str | None = Field(None, alias="sessionType")

    what_to_bring: str | None = Field(None, alias="whatToBring")
    prerequisites: str | None = None

    photo_album_url: str | None = Field(None, alias="photoAlbumUrl")
    internal_notes: str | None = Field(None, alias="internalNotes")
    archived: bool | None = None

    # Block associations (for term-type sessions)
    block_ids: list[str] | None = Field(None, alias="blockIds")


# ---------- Occurrences ----------


class OccurrenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str = Field(..., alias="sessionId")
    starts_at: datetime = Field(..., alias="startsAt")
    ends_at: datetime = Field(..., alias="endsAt")

    cancelled: bool
    cancellation_reason: str | None = Field(None, alias="cancellationReason")

    # Occurrence metadata
    auto_generated: bool = Field(False, alias="autoGenerated")
    block_id: str | None = Field(None, alias="blockId")
    block_name: str | None = Field(None, alias="blockName")


class OccurrenceCreate(BaseModel):
    starts_at: datetime = Field(..., alias="startsAt")
    ends_at: datetime = Field(..., alias="endsAt")
    block_id: str | None = Field(None, alias="blockId")


class OccurrenceCancel(BaseModel):
    cancelled: bool = True
    cancellation_reason: str | None = Field(None, alias="cancellationReason")


# ---------- Signups ----------


class AdminSignupOut(BaseModel):
    id: str
    status: str
    created_at: datetime = Field(..., alias="createdAt")

    session_id: str = Field(..., alias="sessionId")
    child_id: str | None = Field(None, alias="childId")
    caregiver_id: str | None = Field(None, alias="caregiverId")

    student_name: str | None = Field(None, alias="studentName")
    guardian_name: str | None = Field(None, alias="guardianName")
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = Field(None, alias="dateOfBirth")


class SignupStatusUpdate(BaseModel):
    status: Literal["confirmed", "waitlisted", "withdrawn"]


# ---------- Attendance ----------


AttendanceStatus = Literal["present", "absent_known", "absent_unknown"]


class AttendanceRecordOut(BaseModel):
    id: str
    occurrence_id: str = Field(..., alias="occurrenceId")
    child_id: str = Field(..., alias="childId")
    status: AttendanceStatus
    reason: str | None = None


class AttendanceUpsert(BaseModel):
    child_id: str = Field(..., alias="childId")
    status: AttendanceStatus
    reason: str | None = None
    actor: str | None = None


class AttendanceRollItem(BaseModel):
    child_id: str = Field(..., alias="childId")
    child_name: str = Field(..., alias="childName")
    signup_id: str = Field(..., alias="signupId")
    attendance: AttendanceRecordOut | None = None


class AttendanceRollOut(BaseModel):
    occurrence: OccurrenceOut
    items: list[AttendanceRollItem]


# ---------- Children & Notes ----------


class ChildAdminOut(BaseModel):
    """Child information for staff/admin use.

    NOTE: Demographic fields (region, ethnicity, school_name) are deliberately
    excluded from this schema. These fields are only accessible to caregivers
    and system administrators for aggregate reporting purposes.
    """

    id: str
    caregiver_id: str = Field(..., alias="caregiverId")
    name: str
    date_of_birth: date = Field(..., alias="dateOfBirth")
    media_consent: bool = Field(False, alias="mediaConsent")
    medical_info: str | None = Field(None, alias="medicalInfo")
    other_info: str | None = Field(None, alias="otherInfo")


class ChildNoteOut(BaseModel):
    id: str
    childId: str = Field(..., alias="child_id")
    author: str | None = None
    note: str


class ChildNoteCreate(BaseModel):
    note: str = Field(..., min_length=1)
    author: str | None = None


# ---------- Communications / Exports ----------


class BulkEmailRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    actor: str | None = None


class SessionChangeAlertRequest(BaseModel):
    update_title: str = Field(..., min_length=1, alias="updateTitle")
    update_message: str | None = Field(None, alias="updateMessage")
    affected_date: str | None = Field(None, alias="affectedDate")
    actor: str | None = None

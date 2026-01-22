"""Admin routes for staff management."""

from __future__ import annotations

import uuid
from datetime import datetime

from litestar import Controller, get, patch, post
from litestar import delete as http_delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db_session
from app.models.session import Session
from app.models.session_staff import SessionStaff
from app.models.staff import Staff
from app.schemas.staff import (
    SessionStaffAssignment,
    StaffCreate,
    StaffListItem,
    StaffResponse,
    StaffUpdate,
)


class StaffAdminController(Controller):
    """Admin endpoints for managing staff and session assignments."""

    path = "/api/v1/admin/staff"
    tags = ["Admin - Staff"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/", status_code=HTTP_200_OK, summary="List all staff")
    async def list_staff(
        self,
        db: AsyncSession,
        active_only: bool = True,
    ) -> list[StaffListItem]:
        """List all staff members.

        Args:
            active_only: If True, only return active staff members
        """
        stmt = select(Staff)
        if active_only:
            stmt = stmt.where(Staff.active.is_(True))

        result = await db.execute(stmt.order_by(Staff.name))
        staff = result.scalars().all()

        return [
            StaffListItem(
                id=s.id,
                name=s.name,
                email=s.email,
                active=s.active,
            )
            for s in staff
        ]

    @get("/{staff_id:uuid}", status_code=HTTP_200_OK, summary="Get staff member")
    async def get_staff(
        self,
        db: AsyncSession,
        staff_id: uuid.UUID,
    ) -> StaffResponse:
        """Get detailed information about a staff member."""
        result = await db.execute(select(Staff).where(Staff.id == staff_id))
        staff = result.scalar_one_or_none()

        if not staff:
            raise NotFoundException(detail="Staff member not found")

        return StaffResponse.model_validate(staff)

    @post("/", status_code=HTTP_201_CREATED, summary="Create staff member")
    async def create_staff(
        self,
        db: AsyncSession,
        data: StaffCreate,
    ) -> StaffResponse:
        """Create a new staff member (typically called after SSO login).

        This endpoint is used to create a staff record after successful SSO authentication.
        The SSO system provides the name, email, and sso_id.
        """
        # Check if staff already exists by sso_id
        result = await db.execute(select(Staff).where(Staff.sso_id == data.sso_id))
        existing = result.scalar_one_or_none()

        if existing:
            # Update last login time
            existing.last_login_at = datetime.now()
            # Update name/email in case they changed in SSO
            existing.name = data.name
            existing.email = data.email
            await db.commit()
            await db.refresh(existing)
            return StaffResponse.model_validate(existing)

        # Create new staff member
        staff = Staff(
            name=data.name,
            email=data.email,
            sso_id=data.sso_id,
            last_login_at=datetime.now(),
            active=True,
        )

        db.add(staff)
        await db.commit()
        await db.refresh(staff)

        return StaffResponse.model_validate(staff)

    @patch("/{staff_id:uuid}", status_code=HTTP_200_OK, summary="Update staff member")
    async def update_staff(
        self,
        db: AsyncSession,
        staff_id: uuid.UUID,
        data: StaffUpdate,
    ) -> StaffResponse:
        """Update staff member details."""
        result = await db.execute(select(Staff).where(Staff.id == staff_id))
        staff = result.scalar_one_or_none()

        if not staff:
            raise NotFoundException(detail="Staff member not found")

        # Update fields
        if data.name is not None:
            staff.name = data.name
        if data.email is not None:
            staff.email = data.email
        if data.active is not None:
            staff.active = data.active
            if not data.active and staff.deactivated_at is None:
                staff.deactivated_at = datetime.now()
            elif data.active:
                staff.deactivated_at = None

        await db.commit()
        await db.refresh(staff)

        return StaffResponse.model_validate(staff)

    @get(
        "/{staff_id:uuid}/sessions",
        status_code=HTTP_200_OK,
        summary="Get staff's assigned sessions",
    )
    async def get_staff_sessions(
        self,
        db: AsyncSession,
        staff_id: uuid.UUID,
    ) -> list[dict]:
        """Get all sessions assigned to a staff member."""
        result = await db.execute(select(Staff).where(Staff.id == staff_id))
        staff = result.scalar_one_or_none()

        if not staff:
            raise NotFoundException(detail="Staff member not found")

        # Get all sessions assigned to this staff member
        stmt = (
            select(Session)
            .join(SessionStaff, Session.id == SessionStaff.session_id)
            .where(SessionStaff.staff_id == staff_id)
            .options(selectinload(Session.session_location))
            .order_by(Session.year.desc(), Session.name)
        )

        result = await db.execute(stmt)
        sessions = result.scalars().all()

        return [
            {
                "id": str(s.id),
                "name": s.name,
                "year": s.year,
                "session_type": s.session_type,
                "location": s.session_location.name if s.session_location else None,
            }
            for s in sessions
        ]


class SessionStaffController(Controller):
    """Admin endpoints for managing staff assignments to sessions."""

    path = "/api/v1/admin/sessions/{session_id:uuid}/staff"
    tags = ["Admin - Sessions"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/", status_code=HTTP_200_OK, summary="Get session staff assignments")
    async def get_session_staff(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
    ) -> list[StaffListItem]:
        """Get all staff members assigned to a session."""
        # Verify session exists
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException(detail="Session not found")

        # Get assigned staff
        stmt = (
            select(Staff)
            .join(SessionStaff, Staff.id == SessionStaff.staff_id)
            .where(SessionStaff.session_id == session_id)
            .order_by(Staff.name)
        )

        result = await db.execute(stmt)
        staff = result.scalars().all()

        return [
            StaffListItem(
                id=s.id,
                name=s.name,
                email=s.email,
                active=s.active,
            )
            for s in staff
        ]

    @post("/", status_code=HTTP_200_OK, summary="Assign staff to session")
    async def assign_staff(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        data: SessionStaffAssignment,
    ) -> Response:
        """Assign staff members to a session.

        This replaces all existing staff assignments for the session.
        To remove all staff, pass an empty list.
        """
        # Verify session exists
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundException(detail="Session not found")

        # Verify all staff members exist
        if data.staff_ids:
            result = await db.execute(select(Staff.id).where(Staff.id.in_(data.staff_ids)))
            existing_ids = {row[0] for row in result.fetchall()}

            missing_ids = set(data.staff_ids) - existing_ids
            if missing_ids:
                raise NotFoundException(detail=f"Staff members not found: {', '.join(str(id) for id in missing_ids)}")

        # Remove existing assignments
        from sqlalchemy import delete as sql_delete

        await db.execute(sql_delete(SessionStaff).where(SessionStaff.session_id == session_id))

        # Create new assignments
        for staff_id in data.staff_ids:
            assignment = SessionStaff(
                session_id=session_id,
                staff_id=staff_id,
            )
            db.add(assignment)

        await db.commit()

        return Response(
            content={"message": f"Assigned {len(data.staff_ids)} staff member(s) to session"},
            status_code=HTTP_200_OK,
        )

    @http_delete(
        "/{staff_id:uuid}",
        status_code=HTTP_204_NO_CONTENT,
        summary="Remove staff from session",
    )
    async def remove_staff(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        staff_id: uuid.UUID,
    ) -> None:
        """Remove a specific staff member from a session."""
        # Delete the assignment
        from sqlalchemy import delete as sql_delete

        result = await db.execute(
            sql_delete(SessionStaff)
            .where(SessionStaff.session_id == session_id)
            .where(SessionStaff.staff_id == staff_id)
        )

        if result.rowcount == 0:  # type: ignore[attr-defined]
            raise NotFoundException(detail="Staff assignment not found")

        await db.commit()

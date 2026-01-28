from __future__ import annotations

import logging
from uuid import UUID

from litestar import Controller, get, patch, post, delete
from litestar.exceptions import NotFoundException
from litestar.status_codes import HTTP_200_OK


from app.domains.admin.schemas.student import Student, StudentCreate, StudentUpdate


from advanced_alchemy.extensions.litestar import providers, service

logger = logging.getLogger(__name__)

from app.domains.admin.services.student import StudentService

from litestar.params import Dependency, Parameter
from typing import Annotated
from advanced_alchemy.extensions.litestar import filters


class StudentController(Controller):
    """Admin endpoints for managing students."""

    path = "/api/v1/admin/students"
    tags = ["Admin"]
    dependencies = providers.create_service_dependencies(
        StudentService,
        "student_service",
        # enable to filter by region, by min age, by max_age and by location
    )

    @get("/")
    async def list_students(
        self,
        student_service: StudentService,
    ) -> service.OffsetPagination[Student]:
        """List all students."""
        results, total = await student_service.list_and_count()
        return student_service.to_schema(results, total, schema_type=Student)

    @get("/{student_id:uuid}")
    async def get_student(
        self,
        student_id: UUID,
        student_service: StudentService,
    ) -> Student:
        """Get a single student by ID."""
        student = await student_service.get(student_id)
        if not student:
            raise NotFoundException(detail="Student not found")
        return student_service.to_schema(student, schema_type=Student)

    @post("/")
    async def create_student(
        self,
        student_data: StudentCreate,
        student_service: StudentService,
    ) -> Student:
        """Create a new student."""
        student = await student_service.create(student_data)
        return student_service.to_schema(student, schema_type=Student)

    @patch("/{student_id:uuid}")
    async def update_student(
        self,
        student_id: UUID,
        student_data: StudentUpdate,
        student_service: StudentService,
    ) -> Student:
        """Update an existing student."""
        student = await student_service.update(student_id, student_data)
        if not student:
            raise NotFoundException(detail="Student not found")
        return student_service.to_schema(student, schema_type=Student)

    @delete("/{student_id:uuid}", status_code=HTTP_200_OK)
    async def delete_student(
        self,
        student_id: UUID,
        student_service: StudentService,
    ) -> None:
        """Delete a student."""
        deleted = await student_service.delete(student_id)
        if not deleted:
            raise NotFoundException(detail="Student not found")
"""Integration tests for public API endpoints (no authentication required)."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from litestar.status_codes import HTTP_200_OK, HTTP_404_NOT_FOUND
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.session_location import SessionLocation
from app.models.session_occurrence import SessionOccurrence


@pytest_asyncio.fixture
async def test_location(db_session: AsyncSession) -> SessionLocation:
    location = SessionLocation(
        name="Test Hub",
        address="123 Test Street, Auckland",
        region="Auckland",
        lat=-36.8485,
        lng=174.7633,
        contact_name="Test Contact",
        contact_email="test@example.com",
        contact_phone="+6491234567",
    )
    db_session.add(location)
    await db_session.flush()
    await db_session.commit()
    return location


@pytest_asyncio.fixture
async def test_session(db_session: AsyncSession, test_location: SessionLocation) -> Session:
    session = Session(
        session_location_id=test_location.id,
        year=2026,
        session_type="term",
        name="Python Programming",
        age_lower=10,
        age_upper=14,
        day_of_week=0,
        start_time=time(15, 30),
        end_time=time(17, 30),
        waitlist=False,
        capacity=20,
        what_to_bring="Laptop",
        prerequisites="None",
    )
    db_session.add(session)
    await db_session.flush()
    await db_session.commit()
    return session


@pytest_asyncio.fixture
async def test_occurrence(db_session: AsyncSession, test_session: Session) -> SessionOccurrence:
    starts_at = datetime(2026, 2, 1, 2, 30, tzinfo=UTC)
    ends_at = starts_at + timedelta(hours=2)
    occ = SessionOccurrence(
        session_id=test_session.id,
        starts_at=starts_at,
        ends_at=ends_at,
        cancelled=False,
    )
    db_session.add(occ)
    await db_session.flush()
    await db_session.commit()
    return occ


class TestPublicHealth:
    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self, test_client: AsyncTestClient) -> None:
        response = await test_client.get("/api/v1/health")
        assert response.status_code == HTTP_200_OK
        payload = response.json()
        assert payload["status"] == "healthy"


class TestListSessions:
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, test_client: AsyncTestClient) -> None:
        response = await test_client.get("/api/v1/sessions")
        assert response.status_code == HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sessions_grouped_by_region(
        self,
        test_client: AsyncTestClient,
        test_session: Session,
    ) -> None:
        response = await test_client.get("/api/v1/sessions")
        assert response.status_code == HTTP_200_OK

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "Auckland"
        assert isinstance(data[0]["sessions"], list)
        assert len(data[0]["sessions"]) == 1

        session_payload = data[0]["sessions"][0]
        assert session_payload["id"] == str(test_session.id)
        assert session_payload["name"] == "Python Programming"
        assert "locationDetails" in session_payload

    @pytest.mark.asyncio
    async def test_list_sessions_search_query_match(
        self,
        test_client: AsyncTestClient,
        test_session: Session,
    ) -> None:
        response = await test_client.get("/api/v1/sessions?q=Python")
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Auckland"
        assert any(s["id"] == str(test_session.id) for s in data[0]["sessions"])

    @pytest.mark.asyncio
    async def test_list_sessions_search_query_no_match(self, test_client: AsyncTestClient) -> None:
        response = await test_client.get("/api/v1/sessions?q=DoesNotMatch")
        assert response.status_code == HTTP_200_OK
        assert response.json() == []


class TestGetSession:
    @pytest.mark.asyncio
    async def test_get_session_success(
        self,
        test_client: AsyncTestClient,
        test_session: Session,
        test_occurrence: SessionOccurrence,
    ) -> None:
        response = await test_client.get(f"/api/v1/session/{test_session.id}")
        assert response.status_code == HTTP_200_OK

        data = response.json()
        assert data["id"] == str(test_session.id)
        assert data["name"] == "Python Programming"
        assert "locationDetails" in data
        assert "occurrences_by_block" in data
        # occurrences_by_block will be empty if no blocks are linked to the session

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, test_client: AsyncTestClient) -> None:
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/session/{non_existent_id}")
        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_session_invalid_uuid(self, test_client: AsyncTestClient) -> None:
        response = await test_client.get("/api/v1/session/not-a-uuid")
        assert response.status_code in (400, 404)


class TestSessionCalendar:
    @pytest.mark.asyncio
    async def test_download_calendar_success(
        self,
        test_client: AsyncTestClient,
        test_session: Session,
        test_occurrence: SessionOccurrence,
    ) -> None:
        response = await test_client.get(f"/api/v1/session/{test_session.id}/calendar.ics")
        assert response.status_code == HTTP_200_OK
        assert "text/calendar" in response.headers.get("content-type", "")

        ics_content = response.text
        assert "BEGIN:VCALENDAR" in ics_content
        assert "END:VCALENDAR" in ics_content
        assert "Python Programming" in ics_content

    @pytest.mark.asyncio
    async def test_download_calendar_not_found(self, test_client: AsyncTestClient) -> None:
        non_existent_id = uuid4()
        response = await test_client.get(f"/api/v1/session/{non_existent_id}/calendar.ics")
        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_download_calendar_content_disposition(
        self,
        test_client: AsyncTestClient,
        test_session: Session,
        test_occurrence: SessionOccurrence,
    ) -> None:
        response = await test_client.get(f"/api/v1/session/{test_session.id}/calendar.ics")
        assert response.status_code == HTTP_200_OK
        content_disposition = response.headers.get("content-disposition") or response.headers.get("Content-Disposition")
        assert content_disposition is not None

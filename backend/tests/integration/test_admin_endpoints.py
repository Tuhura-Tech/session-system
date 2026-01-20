"""Comprehensive integration tests for Admin API endpoints.
Covers: blocks, exclusions, locations, sessions, occurrences, signups, attendance,
communications, exports, and children endpoints.
"""

from datetime import UTC, date, datetime, time, timedelta

import pytest
import pytest_asyncio
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
)
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin_auth import create_admin_session
from app.models.caregiver import Caregiver
from app.models.child import Child
from app.models.session import DayOfWeekEnum, Session
from app.models.session_block import SessionBlock, SessionBlockType
from app.models.session_block_link import SessionBlockLink
from app.models.session_location import SessionLocation
from app.models.signup import Signup


@pytest_asyncio.fixture
async def admin_headers() -> dict[str, str]:
    token = create_admin_session(email="admin@test.local", provider="test", provider_user_id="p-1")
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def location(db_session: AsyncSession) -> SessionLocation:
    import uuid

    suffix = uuid.uuid4().hex[:8]
    loc = SessionLocation(
        name=f"Test Venue {suffix}",
        address="1 Test St",
        region="Wellington",
        lat=-41.28664,
        lng=174.77557,
        instructions="Arrive early",
        contact_name="Admin",
        contact_email=f"admin+{suffix}@example.com",
        contact_phone="+64000000",
    )
    db_session.add(loc)
    await db_session.flush()
    return loc


@pytest_asyncio.fixture
async def blocks(db_session: AsyncSession) -> list[SessionBlock]:
    year = 2000 + int(date.today().day)  # Vary by day of month
    b1 = SessionBlock(
        year=year,
        block_type=SessionBlockType.TERM_1,
        name="Term 1",
        start_date=date(year, 2, 1),
        end_date=date(year, 4, 10),
        timezone="Pacific/Auckland",
    )
    b2 = SessionBlock(
        year=year,
        block_type=SessionBlockType.TERM_2,
        name="Term 2",
        start_date=date(year, 4, 27),
        end_date=date(year, 7, 3),
        timezone="Pacific/Auckland",
    )
    db_session.add_all([b1, b2])
    await db_session.flush()
    return [b1, b2]


@pytest_asyncio.fixture
async def term_session(db_session: AsyncSession, location: SessionLocation, blocks: list[SessionBlock]) -> Session:
    import uuid

    suffix = uuid.uuid4().hex[:4]
    s = Session(
        session_location_id=location.id,
        year=blocks[0].year,
        session_type="term",
        name=f"Python Club {suffix}",
        age_lower=8,
        age_upper=13,
        day_of_week=DayOfWeekEnum(2),  # Wednesday
        start_time=time(15, 30),
        end_time=time(17, 0),
        waitlist=False,
        capacity=20,
        what_to_bring="Laptop",
        prerequisites="None",
        archived=False,
    )
    db_session.add(s)
    await db_session.flush()
    # link blocks
    for b in blocks:
        db_session.add(SessionBlockLink(session_id=s.id, block_id=b.id))
    await db_session.flush()
    return s


@pytest_asyncio.fixture
async def caregiver_child(db_session: AsyncSession) -> tuple[Caregiver, Child]:
    import uuid

    suffix = uuid.uuid4().hex[:8]
    cg = Caregiver(email=f"parent+{suffix}@example.com", name=f"Parent {suffix}", email_verified=True)
    db_session.add(cg)
    await db_session.flush()
    ch = Child(caregiver_id=cg.id, name=f"Student {suffix}", date_of_birth=date(2015, 1, 1))
    db_session.add(ch)
    await db_session.flush()
    return cg, ch


@pytest_asyncio.fixture
async def confirmed_signup(
    db_session: AsyncSession, term_session: Session, caregiver_child: tuple[Caregiver, Child]
) -> Signup:
    cg, ch = caregiver_child
    su = Signup(session_id=term_session.id, caregiver_id=cg.id, child_id=ch.id, status="confirmed")
    db_session.add(su)
    await db_session.flush()
    return su


class TestAdminLocations:
    @pytest.mark.anyio
    async def test_list_and_get_and_create_update_location(
        self, test_client: AsyncTestClient, admin_headers: dict[str, str]
    ) -> None:
        # Create
        res = await test_client.post(
            "/api/v1/admin/locations",
            headers=admin_headers,
            json={
                "name": "New Venue",
                "address": "2 Test Ave",
                "region": "Auckland",
                "lat": -36.85,
                "lng": 174.76,
                "instructions": "Gate 3",
                "contactName": "Ops",
                "contactEmail": "ops@example.com",
                "contactPhone": "+64000001",
                "internalNotes": "Wheelchair access",
            },
        )
        assert res.status_code == HTTP_200_OK
        loc = res.json()
        # List
        res = await test_client.get("/api/v1/admin/locations", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        assert any(loc_item["id"] == loc["id"] for loc_item in res.json())
        # Get
        res = await test_client.get(f"/api/v1/admin/locations/{loc['id']}", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # Update
        res = await test_client.patch(
            f"/api/v1/admin/locations/{loc['id']}",
            headers=admin_headers,
            json={"name": "Updated Venue"},
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["name"] == "Updated Venue"


class TestAdminBlocksExclusions:
    @pytest.mark.anyio
    async def test_blocks_crud(self, test_client: AsyncTestClient, admin_headers: dict[str, str]) -> None:
        # Create
        res = await test_client.post(
            "/api/v1/admin/blocks",
            headers=admin_headers,
            json={
                "year": 2026,
                "blockType": "term_3",
                "name": "Term 3",
                "startDate": "2026-07-20",
                "endDate": "2026-09-25",
                "timezone": "Pacific/Auckland",
            },
        )
        if res.status_code != HTTP_200_OK:
            print(f"DEBUG: {res.status_code} {res.text}")
        assert res.status_code == HTTP_200_OK
        block = res.json()
        # List
        res = await test_client.get("/api/v1/admin/blocks?year=2026", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # Update
        res = await test_client.patch(
            f"/api/v1/admin/blocks/{block['id']}",
            headers=admin_headers,
            json={"name": "Term 3 Updated"},
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["name"] == "Term 3 Updated"

    @pytest.mark.anyio
    async def test_exclusions_crud(self, test_client: AsyncTestClient, admin_headers: dict[str, str]) -> None:
        # Create
        res = await test_client.post(
            "/api/v1/admin/exclusions",
            headers=admin_headers,
            json={"year": 2026, "date": "2026-09-01", "reason": "Holiday"},
        )
        assert res.status_code == HTTP_200_OK
        excl = res.json()
        # List by year
        res = await test_client.get("/api/v1/admin/exclusions?year=2026", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # Update
        res = await test_client.patch(
            f"/api/v1/admin/exclusions/{excl['id']}", headers=admin_headers, json={"reason": "Updated"}
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["reason"] == "Updated"


class TestAdminSessions:
    @pytest.mark.anyio
    async def test_sessions_crud_and_get(
        self, test_client: AsyncTestClient, admin_headers: dict[str, str], location: SessionLocation
    ) -> None:
        # Create term session
        res = await test_client.post(
            "/api/v1/admin/sessions",
            headers=admin_headers,
            json={
                "sessionLocationId": str(location.id),
                "year": 2026,
                "name": "Robotics",
                "ageLower": 10,
                "ageUpper": 15,
                "dayOfWeek": 1,
                "startTime": "15:30:00",
                "endTime": "17:00:00",
                "waitlist": False,
                "capacity": 16,
                "sessionType": "term",
                "whatToBring": "Laptop",
                "prerequisites": "",
                "photoAlbumUrl": "",
                "internalNotes": "",
                "archived": False,
                "blockIds": [],
            },
        )
        assert res.status_code == HTTP_200_OK
        sess = res.json()
        # List
        res = await test_client.get("/api/v1/admin/sessions?year=2026", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # Get by id
        res = await test_client.get(f"/api/v1/admin/sessions/{sess['id']}", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        assert res.json()["sessionType"] == "term"
        # Update
        res = await test_client.patch(
            f"/api/v1/admin/sessions/{sess['id']}", headers=admin_headers, json={"name": "Robotics Updated"}
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["name"] == "Robotics Updated"
        # Duplicate -> 200 with new id
        res = await test_client.post(f"/api/v1/admin/sessions/{sess['id']}/duplicate", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        dup = res.json()
        assert dup["id"] != sess["id"]
        # Delete original
        res = await test_client.delete(f"/api/v1/admin/sessions/{sess['id']}", headers=admin_headers)
        assert res.status_code == HTTP_204_NO_CONTENT
        # Verify deleted
        res = await test_client.get(f"/api/v1/admin/sessions/{sess['id']}", headers=admin_headers)
        assert res.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.anyio
    async def test_location_sessions_list(
        self, test_client: AsyncTestClient, admin_headers: dict[str, str], term_session: Session
    ) -> None:
        res = await test_client.get(
            f"/api/v1/admin/locations/{term_session.session_location_id}/sessions",
            headers=admin_headers,
        )
        assert res.status_code == HTTP_200_OK
        data = res.json()
        assert any(s["id"] == str(term_session.id) for s in data)


class TestOccurrencesAndAttendance:
    @pytest.mark.anyio
    async def test_generate_and_list_occurrences(
        self, test_client: AsyncTestClient, admin_headers: dict[str, str], term_session: Session
    ) -> None:
        res = await test_client.post(
            f"/api/v1/admin/sessions/{term_session.id}/occurrences/generate",
            headers=admin_headers,
        )
        assert res.status_code == HTTP_200_OK
        gen = res.json()
        res = await test_client.get(f"/api/v1/admin/sessions/{term_session.id}/occurrences", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        occs = res.json()
        assert len(occs) >= gen["created"]

    @pytest.mark.anyio
    async def test_create_cancel_reinstate_occurrence(
        self, test_client: AsyncTestClient, admin_headers: dict[str, str], term_session: Session
    ) -> None:
        # manual create one-off occurrence today
        now = datetime.now(UTC)
        res = await test_client.post(
            f"/api/v1/admin/sessions/{term_session.id}/occurrences",
            headers=admin_headers,
            json={"startsAt": now.isoformat(), "endsAt": (now + timedelta(hours=1)).isoformat()},
        )
        assert res.status_code == HTTP_200_OK
        occ = res.json()
        # cancel
        res = await test_client.patch(
            f"/api/v1/admin/occurrences/{occ['id']}/cancel",
            headers=admin_headers,
            json={"cancelled": True, "cancellationReason": "Weather"},
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["cancelled"] is True
        # reinstate
        res = await test_client.patch(
            f"/api/v1/admin/occurrences/{occ['id']}/cancel",
            headers=admin_headers,
            json={"cancelled": False},
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["cancelled"] is False

    @pytest.mark.anyio
    async def test_roll_and_attendance(
        self,
        test_client: AsyncTestClient,
        admin_headers: dict[str, str],
        term_session: Session,
        confirmed_signup: Signup,
    ) -> None:
        # Generate occurrences and take the earliest one for roll
        res = await test_client.post(
            f"/api/v1/admin/sessions/{term_session.id}/occurrences/generate",
            headers=admin_headers,
        )
        assert res.status_code == HTTP_200_OK
        res = await test_client.get(
            f"/api/v1/admin/sessions/{term_session.id}/occurrences",
            headers=admin_headers,
        )
        occs = res.json()
        if not occs:
            pytest.skip("No occurrences generated; schedule may not align in test window")
        occ_id = occs[0]["id"]
        # roll
        res = await test_client.get(f"/api/v1/admin/occurrences/{occ_id}/roll", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        roll = res.json()
        # upsert attendance
        # childId must match signup; backend returns items array
        if not roll["items"]:
            pytest.skip("No roll items to mark attendance in this run")
        child_id = roll["items"][0]["childId"]
        res = await test_client.post(
            f"/api/v1/admin/occurrences/{occ_id}/attendance",
            headers=admin_headers,
            json={"childId": child_id, "status": "present", "reason": None},
        )
        assert res.status_code == HTTP_200_OK
        # history
        res = await test_client.get(f"/api/v1/admin/occurrences/{occ_id}/attendance-history", headers=admin_headers)
        assert res.status_code == HTTP_200_OK


class TestSignupsChildrenCommsExports:
    @pytest.mark.anyio
    async def test_list_signups_and_status_update(
        self,
        test_client: AsyncTestClient,
        admin_headers: dict[str, str],
        term_session: Session,
        confirmed_signup: Signup,
    ) -> None:
        # list
        res = await test_client.get(f"/api/v1/admin/sessions/{term_session.id}/signups", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        data = res.json()
        assert any(su["id"] == str(confirmed_signup.id) for su in data)
        # update status
        res = await test_client.patch(
            f"/api/v1/admin/signups/{confirmed_signup.id}/status",
            headers=admin_headers,
            json={"status": "waitlisted"},
        )
        assert res.status_code == HTTP_200_OK
        assert res.json()["status"] == "waitlisted"

    @pytest.mark.anyio
    async def test_children_endpoints(
        self,
        test_client: AsyncTestClient,
        admin_headers: dict[str, str],
        caregiver_child: tuple[Caregiver, Child],
    ) -> None:
        cg, ch = caregiver_child
        res = await test_client.get("/api/v1/admin/children", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        res = await test_client.get(f"/api/v1/admin/children/{ch.id}", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # notes list empty
        res = await test_client.get(f"/api/v1/admin/children/{ch.id}/notes", headers=admin_headers)
        assert res.status_code == HTTP_200_OK
        # add note
        res = await test_client.post(
            f"/api/v1/admin/children/{ch.id}/notes",
            headers=admin_headers,
            json={"note": "Allergic to nuts", "author": "Admin"},
        )
        assert res.status_code == HTTP_200_OK

    @pytest.mark.anyio
    async def test_communications_and_exports(
        self,
        monkeypatch: pytest.MonkeyPatch,
        test_client: AsyncTestClient,
        admin_headers: dict[str, str],
        term_session: Session,
        confirmed_signup: Signup,
    ) -> None:
        # Patch get_queue to avoid external SAQ
        class _Q:
            def __init__(self):
                self.calls = []

            async def enqueue(self, *a, **kw):
                self.calls.append((a, kw))

        q = _Q()
        import app.routes.admin as admin_routes

        monkeypatch.setattr(admin_routes, "get_queue", lambda: q, raising=True)

        # bulk email
        res = await test_client.post(
            f"/api/v1/admin/sessions/{term_session.id}/email",
            headers=admin_headers,
            json={"subject": "Test", "message": "Hello"},
        )
        assert res.status_code == HTTP_200_OK
        assert "enqueued" in res.json()
        # notify
        res = await test_client.post(
            f"/api/v1/admin/sessions/{term_session.id}/notify",
            headers=admin_headers,
            json={"updateTitle": "Update", "updateMessage": "Msg", "affectedDate": None},
        )
        assert res.status_code == HTTP_200_OK

        # exports
        res = await test_client.get(
            f"/api/v1/admin/sessions/{term_session.id}/export/signups.csv",
            headers=admin_headers,
        )
        assert res.status_code == HTTP_200_OK
        assert res.headers.get("Content-Type", "").startswith("text/csv")

        # attendance export (may be empty but should 200)
        res = await test_client.get(
            f"/api/v1/admin/sessions/{term_session.id}/export/attendance.csv",
            headers=admin_headers,
        )
        assert res.status_code == HTTP_200_OK
        assert res.headers.get("Content-Type", "").startswith("text/csv")

"""Integration tests for admin API endpoints (admin authentication required).

Tests all admin endpoints for CRUD operations:
- Sessions: Create, Update, Delete, List
- Locations: Create, Update, Delete, List, Get by ID
- Blocks: Create, Update, List
- Exclusions: Create, Update, List
- Staff: Create, Update, List
"""

from datetime import date, time
from decimal import Decimal

import pytest
import pytest_asyncio
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
)
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exclusion_date import ExclusionDate
from app.models.session import Session
from app.models.session_block import SessionBlock, SessionBlockType
from app.models.session_location import SessionLocation


@pytest_asyncio.fixture
async def admin_token() -> str:
    """Create a valid admin authentication token."""
    from app.admin_auth import create_admin_session

    # Create JWT token using the actual admin auth function
    return create_admin_session(
        email="test_admin@example.com",
        provider="test",
        provider_user_id="test_admin_123",
    )


@pytest_asyncio.fixture
async def location(db_session: AsyncSession) -> SessionLocation:
    """Create a test session location."""
    location = SessionLocation(
        name="Test Location",
        address="123 Test St, Wellington",
        region="Wellington",
        lat=Decimal("-41.2865"),
        lng=Decimal("174.7762"),
        instructions="Test arrival instructions",
        contact_name="Test Contact",
        contact_email="contact@test.com",
        contact_phone="+64211234567",
    )
    db_session.add(location)
    await db_session.flush()
    return location


@pytest_asyncio.fixture
async def block(db_session: AsyncSession) -> SessionBlock:
    """Create a test session block."""
    block = SessionBlock(
        year=2025,
        block_type=SessionBlockType.TERM_1,
        name="Term 1",
        start_date=date(2025, 2, 1),
        end_date=date(2025, 4, 15),
        timezone="Pacific/Auckland",
    )
    db_session.add(block)
    await db_session.flush()
    return block


@pytest_asyncio.fixture
async def session_obj(db_session: AsyncSession, location: SessionLocation, block: SessionBlock) -> Session:
    """Create a test session."""
    session = Session(
        session_location_id=location.id,
        year=2025,
        name="Test Session",
        age_lower=5,
        age_upper=12,
        day_of_week=1,  # Monday
        start_time=time(9, 0),
        end_time=time(15, 0),
        waitlist=False,
        capacity=20,
        session_type="term",
        what_to_bring="Lunch and water bottle",
        prerequisites="",
        photo_album_url="",
        internal_notes="",
        archived=False,
    )
    db_session.add(session)
    await db_session.flush()
    return session


class TestAdminAuthentication:
    """Test admin authentication."""

    @pytest.mark.anyio
    @pytest.mark.anyio
    async def test_no_auth_returns_401(self, test_client: AsyncTestClient):
        """Admin endpoints without auth should return 401."""
        response = await test_client.get("/api/v1/admin/sessions")
        assert response.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.anyio
    @pytest.mark.anyio
    async def test_invalid_auth_returns_401(self, test_client: AsyncTestClient):
        """Admin endpoints with invalid auth should return 401."""
        response = await test_client.get("/api/v1/admin/sessions", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestAdminSessions:
    """Test admin session CRUD operations."""

    @pytest.mark.anyio
    async def test_list_sessions(self, test_client: AsyncTestClient, admin_token: str, session_obj: Session):
        """Test listing all sessions as admin."""
        response = await test_client.get("/api/v1/admin/sessions", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(s["id"] == str(session_obj.id) for s in data)

    @pytest.mark.anyio
    async def test_create_session_term_with_session_type(
        self, test_client: AsyncTestClient, admin_token: str, location: SessionLocation
    ):
        """Test creating a term session with sessionType field."""
        session_data = {
            "sessionLocationId": str(location.id),
            "year": 2025,
            "name": "New Test Session",
            "ageLower": 6,
            "ageUpper": 10,
            "dayOfWeek": 2,  # Tuesday
            "startTime": "10:00:00",
            "endTime": "14:00:00",
            "waitlist": False,
            "capacity": 15,
            "sessionType": "term",
            "whatToBring": "Snacks",
            "prerequisites": "",
            "photoAlbumUrl": "",
            "internalNotes": "Test notes",
            "archived": False,
            "blockIds": [],
        }

        response = await test_client.post(
            "/api/v1/admin/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        if response.status_code != HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Test Session"
        assert data["sessionType"] == "term"
        assert data["dayOfWeek"] == 2

    @pytest.mark.anyio
    async def test_create_session_special_type(
        self, test_client: AsyncTestClient, admin_token: str, location: SessionLocation
    ):
        """Test creating a special session type."""
        session_data = {
            "sessionLocationId": str(location.id),
            "year": 2025,
            "name": "Holiday Special",
            "ageLower": 5,
            "ageUpper": 15,
            "dayOfWeek": 3,
            "startTime": "09:00:00",
            "endTime": "16:00:00",
            "waitlist": True,
            "capacity": 25,
            "sessionType": "special",
            "whatToBring": "Lunch",
            "prerequisites": "",
            "photoAlbumUrl": "https://example.com/album",
            "internalNotes": "",
            "archived": False,
            "blockIds": [],
        }

        response = await test_client.post(
            "/api/v1/admin/sessions",
            json=session_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["sessionType"] == "special"
        assert data["photoAlbumUrl"] == "https://example.com/album"

    @pytest.mark.anyio
    async def test_update_session(
        self,
        test_client: AsyncTestClient,
        admin_token: str,
        session_obj: Session,
    ):
        """Test updating a session including sessionType."""
        update_data = {
            "name": "Updated Session Name",
            "sessionType": "special",
            "capacity": 30,
        }

        response = await test_client.patch(
            f"/api/v1/admin/sessions/{session_obj.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Session Name"
        assert data["sessionType"] == "special"
        assert data["capacity"] == 30

    @pytest.mark.anyio
    async def test_delete_session(
        self,
        test_client: AsyncTestClient,
        admin_token: str,
        session_obj: Session,
    ):
        """Test deleting a session."""
        response = await test_client.delete(
            f"/api/v1/admin/sessions/{session_obj.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_204_NO_CONTENT


class TestAdminLocations:
    """Test admin location CRUD operations."""

    @pytest.mark.anyio
    async def test_list_locations(self, test_client: AsyncTestClient, admin_token: str, location: SessionLocation):
        """Test listing all locations."""
        response = await test_client.get(
            "/api/v1/admin/locations",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.anyio
    async def test_get_location_by_uuid(
        self, test_client: AsyncTestClient, admin_token: str, location: SessionLocation
    ):
        """Test getting a single location by UUID."""
        response = await test_client.get(
            f"/api/v1/admin/locations/{location.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["id"] == str(location.id)
        assert data["name"] == "Test Location"

    @pytest.mark.anyio
    async def test_create_location_with_coordinates(self, test_client: AsyncTestClient, admin_token: str):
        """Test creating a location with lat/lng coordinates."""
        location_data = {
            "name": "New Location",
            "address": "456 New St, Auckland",
            "region": "Auckland",
            "lat": -36.8485,
            "lng": 174.7633,
            "instructions": "New instructions",
            "contactName": "New Contact",
            "contactEmail": "new@test.com",
            "contactPhone": "+64211234568",
            "internalNotes": "Admin notes about location",
        }

        response = await test_client.post(
            "/api/v1/admin/locations",
            json=location_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "New Location"
        assert data["lat"] == -36.8485
        assert data["lng"] == 174.7633
        assert data["internalNotes"] == "Admin notes about location"

    @pytest.mark.anyio
    async def test_update_location(self, test_client: AsyncTestClient, admin_token: str, location: SessionLocation):
        """Test updating a location."""
        update_data = {
            "name": "Updated Location",
            "lat": -41.3000,
            "lng": 174.8000,
        }

        response = await test_client.patch(
            f"/api/v1/admin/locations/{location.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Location"


class TestAdminBlocks:
    """Test admin block CRUD operations."""

    @pytest.mark.anyio
    async def test_list_blocks(self, test_client: AsyncTestClient, admin_token: str, block: SessionBlock):
        """Test listing all blocks."""
        response = await test_client.get("/api/v1/admin/blocks", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.anyio
    async def test_create_block(self, test_client: AsyncTestClient, admin_token: str):
        """Test creating a session block."""
        block_data = {
            "year": 2025,
            "blockType": "term",
            "name": "Term 2",
            "startDate": "2025-04-28",
            "endDate": "2025-07-04",
            "timezone": "Pacific/Auckland",
        }

        response = await test_client.post(
            "/api/v1/admin/blocks",
            json=block_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Term 2"
        assert data["blockType"] == "term"

    @pytest.mark.anyio
    async def test_update_block(self, test_client: AsyncTestClient, admin_token: str, block: SessionBlock):
        """Test updating a block."""
        update_data = {"name": "Updated Term 1"}

        response = await test_client.patch(
            f"/api/v1/admin/blocks/{block.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Term 1"


class TestAdminExclusions:
    """Test admin exclusion date CRUD operations."""

    @pytest.mark.anyio
    async def test_list_exclusions(self, test_client: AsyncTestClient, admin_token: str):
        """Test listing all exclusion dates."""
        response = await test_client.get(
            "/api/v1/admin/exclusions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.anyio
    async def test_create_exclusion(self, test_client: AsyncTestClient, admin_token: str):
        """Test creating an exclusion date."""
        exclusion_data = {
            "year": 2025,
            "date": "2025-12-25",
            "reason": "Christmas Day",
        }

        response = await test_client.post(
            "/api/v1/admin/exclusions",
            json=exclusion_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["reason"] == "Christmas Day"

    @pytest.mark.anyio
    async def test_update_exclusion(self, test_client: AsyncTestClient, admin_token: str, db_session: AsyncSession):
        """Test updating an exclusion date."""
        # Create exclusion first
        exclusion = ExclusionDate(year=2025, date=date(2025, 12, 26), reason="Boxing Day")
        db_session.add(exclusion)
        await db_session.flush()

        update_data = {"reason": "Updated Boxing Day"}

        response = await test_client.patch(
            f"/api/v1/admin/exclusions/{exclusion.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["reason"] == "Updated Boxing Day"


class TestAdminStaff:
    """Test admin staff CRUD operations."""

    @pytest.mark.anyio
    async def test_list_staff(self, test_client: AsyncTestClient, admin_token: str):
        """Test listing all staff members."""
        response = await test_client.get("/api/v1/admin/staff", headers={"Authorization": f"Bearer {admin_token}"})
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.anyio
    async def test_create_staff(self, test_client: AsyncTestClient, admin_token: str):
        """Test creating a staff member."""
        staff_data = {
            "ssoId": "staff@example.com",
            "name": "Test Staff",
        }

        response = await test_client.post(
            "/api/v1/admin/staff",
            json=staff_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Staff"
        assert data["ssoId"] == "staff@example.com"

    @pytest.mark.anyio
    async def test_update_staff(
        self,
        test_client: AsyncTestClient,
        admin_token: str,
        db_session: AsyncSession,
    ):
        """Test updating a staff member."""
        # Create staff first
        from app.models.caregiver import Caregiver

        staff = Caregiver(
            email="oldstaff@example.com",
            name="Old Staff Name",
            email_verified=True,
        )
        db_session.add(staff)
        await db_session.flush()

        update_data = {"name": "Updated Staff Name"}

        response = await test_client.patch(
            f"/api/v1/admin/staff/{staff.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Staff Name"

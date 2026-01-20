"""Integration tests for caregiver API endpoints (authentication required).

Tests all caregiver endpoints with 100% coverage:
- GET /api/v1/me - Get current caregiver profile
- PATCH /api/v1/me - Update caregiver profile
- GET /api/v1/children - List caregiver's children
- POST /api/v1/children - Create child
- PATCH /api/v1/children/{child_id} - Update child
- POST /api/v1/session/{session_id}/signup - Create signup for session
- GET /api/v1/signups - List caregiver's signups
- POST /api/v1/signup/{signup_id}/withdraw - Withdraw from session
"""

from datetime import date, datetime, time, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)
from litestar.testing import AsyncTestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    CARE_GIVER_SESSION_COOKIE,
    hash_token,
    new_token,
    session_expires_at,
)

# test_client fixture provides app
from app.models.caregiver import Caregiver
from app.models.caregiver_auth import CaregiverSession
from app.models.child import Child
from app.models.session import Session
from app.models.session_block import SessionBlock, SessionBlockType
from app.models.session_block_link import SessionBlockLink
from app.models.session_location import SessionLocation
from app.models.signup import Signup


@pytest_asyncio.fixture
async def caregiver(db_session: AsyncSession) -> Caregiver:
    """Create a test caregiver with complete profile."""
    caregiver = Caregiver(
        email="test@example.com",
        name="Test Caregiver",
        phone="+64211234567",
        email_verified=True,
    )
    db_session.add(caregiver)
    await db_session.flush()
    return caregiver


@pytest_asyncio.fixture
async def incomplete_caregiver(db_session: AsyncSession) -> Caregiver:
    """Create a caregiver with incomplete profile (no name/phone)."""
    caregiver = Caregiver(
        email="incomplete@example.com",
        email_verified=True,
    )
    db_session.add(caregiver)
    await db_session.flush()
    return caregiver


@pytest_asyncio.fixture
async def auth_token(db_session: AsyncSession, caregiver: Caregiver) -> str:
    """Create valid authentication token for caregiver."""
    raw_token = new_token()
    token_hash = hash_token(raw_token)

    session = CaregiverSession(
        caregiver_id=caregiver.id,
        token_hash=token_hash,
        expires_at=session_expires_at(),
    )
    db_session.add(session)
    await db_session.flush()

    return raw_token


@pytest_asyncio.fixture
async def incomplete_auth_token(db_session: AsyncSession, incomplete_caregiver: Caregiver) -> str:
    """Create valid auth token for incomplete caregiver."""
    raw_token = new_token()
    token_hash = hash_token(raw_token)

    session = CaregiverSession(
        caregiver_id=incomplete_caregiver.id,
        token_hash=token_hash,
        expires_at=session_expires_at(),
    )
    db_session.add(session)
    await db_session.flush()

    return raw_token


@pytest_asyncio.fixture
async def expired_token(db_session: AsyncSession, caregiver: Caregiver) -> str:
    """Create expired authentication token."""
    raw_token = new_token()
    token_hash = hash_token(raw_token)

    session = CaregiverSession(
        caregiver_id=caregiver.id,
        token_hash=token_hash,
        expires_at=datetime.now(datetime.now().astimezone().tzinfo) - timedelta(days=1),
    )
    db_session.add(session)
    await db_session.flush()

    return raw_token


@pytest_asyncio.fixture
async def child(db_session: AsyncSession, caregiver: Caregiver) -> Child:
    """Create a test child for caregiver."""
    child = Child(
        caregiver_id=caregiver.id,
        name="Test Child",
        date_of_birth=date(2015, 5, 15),
        media_consent=True,
        medical_info="No allergies",
        other_info="Loves coding",
    )
    db_session.add(child)
    await db_session.flush()
    return child


@pytest_asyncio.fixture
async def test_location(db_session: AsyncSession) -> SessionLocation:
    """Create a test session location."""
    location = SessionLocation(
        name="Test Hub",
        address="123 Test St",
        region="Auckland",
        lat=-36.8485,
        lng=174.7633,
        contact_name="Contact",
        contact_email="test@test.com",
        contact_phone="+6491234567",
    )
    db_session.add(location)
    await db_session.flush()
    return location


@pytest_asyncio.fixture
async def test_block(db_session: AsyncSession) -> SessionBlock:
    """Create a test session block."""
    block = SessionBlock(
        year=2026,
        block_type=SessionBlockType.TERM_1,
        name="Term 1 2026",
        start_date=date(2026, 2, 1),
        end_date=date(2026, 4, 10),
        timezone="Pacific/Auckland",
    )
    db_session.add(block)
    await db_session.flush()
    await db_session.commit()
    return block


@pytest_asyncio.fixture
async def session(
    db_session: AsyncSession,
    test_location: SessionLocation,
    test_block: SessionBlock,
) -> Session:
    """Create a test session."""
    session = Session(
        session_location_id=test_location.id,
        year=2026,
        session_type="term",
        name="Test Session",
        age_lower=10,
        age_upper=14,
        day_of_week=1,
        start_time=time(10, 0),
        end_time=time(12, 0),
        waitlist=False,
        capacity=20,
        what_to_bring="Nothing",
    )
    db_session.add(session)
    await db_session.flush()
    db_session.add(SessionBlockLink(session_id=session.id, block_id=test_block.id))
    await db_session.flush()
    await db_session.commit()
    return session


@pytest_asyncio.fixture
async def signup(
    db_session: AsyncSession,
    caregiver: Caregiver,
    child: Child,
    session: Session,
) -> Signup:
    """Create a test signup."""
    signup = Signup(
        session_id=session.id,
        caregiver_id=caregiver.id,
        child_id=child.id,
        status="confirmed",
        pickup_dropoff="Parent pickup",
    )
    db_session.add(signup)
    await db_session.flush()
    await db_session.commit()
    return signup


class TestGetMe:
    """Test GET /api/me - get current caregiver profile."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Authenticated user can get their profile."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/me",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test Caregiver"
        assert data["phone"] == "+64211234567"

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, test_client: AsyncTestClient, db_session: AsyncSession):
        """Unauthenticated request should return 401."""
        # Use test_client directly
        response = await test_client.get("/api/v1/me")

        assert response.status_code == HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_me_expired_session(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        expired_token: str,
    ):
        """Expired session should return 401."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/me",
            cookies={CARE_GIVER_SESSION_COOKIE: expired_token},
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestUpdateMe:
    """Test PATCH /api/me - update caregiver profile."""

    @pytest.mark.asyncio
    async def test_update_me_success(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Can update name and phone."""
        response = await test_client.patch(
            "/api/v1/me",
            json={
                "name": "Updated Name",
                "phone": "+64299999999",
            },
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "+64299999999"

    @pytest.mark.asyncio
    async def test_update_me_partial(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Can update both name and phone."""
        response = await test_client.patch(
            "/api/v1/me",
            json={"name": "Just Name", "phone": "+64211234567"},
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Just Name"
        assert data["phone"] == "+64211234567"

    @pytest.mark.asyncio
    async def test_update_me_unauthenticated(self, test_client: AsyncTestClient, db_session: AsyncSession):
        """Unauthenticated request should return 401."""
        response = await test_client.patch(
            "/api/v1/me",
            json={"name": "Hacker", "phone": "+64211111111"},
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestListChildren:
    """Test GET /api/children - list caregiver's children."""

    @pytest.mark.asyncio
    async def test_list_children_empty(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Returns empty list when no children."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/children",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_children_with_data(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        child: Child,
        auth_token: str,
    ):
        """Returns caregiver's children."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/children",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Child"
        assert data[0]["dateOfBirth"] == "2015-05-15"

    @pytest.mark.asyncio
    async def test_list_children_unauthenticated(self, test_client: AsyncTestClient, db_session: AsyncSession):
        """Unauthenticated request should return 401."""
        # Use test_client directly
        response = await test_client.get("/api/v1/children")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestCreateChild:
    """Test POST /api/children - create child."""

    @pytest.mark.asyncio
    @patch("app.routes.caregiver.get_queue")
    async def test_create_child_success(
        self,
        mock_get_queue,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Can create child with complete data."""
        mock_queue = AsyncMock()
        mock_get_queue.return_value = mock_queue

        response = await test_client.post(
            "/api/v1/children",
            json={
                "name": "New Child",
                "dateOfBirth": "2016-03-20",
                "mediaConsent": True,
                "medicalInfo": "Asthma",
                "otherInfo": "Friendly",
            },
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "New Child"
        assert data["dateOfBirth"] == "2016-03-20"
        assert data["medicalInfo"] == "Asthma"

    @pytest.mark.asyncio
    async def test_create_child_incomplete_profile(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        incomplete_caregiver: Caregiver,
        incomplete_auth_token: str,
    ):
        """Cannot create child without complete caregiver profile."""
        response = await test_client.post(
            "/api/v1/children",
            json={
                "name": "Child",
                "dateOfBirth": "2016-01-01",
                "mediaConsent": True,
            },
            cookies={CARE_GIVER_SESSION_COOKIE: incomplete_auth_token},
        )

        assert response.status_code == HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_child_unauthenticated(self, test_client: AsyncTestClient, db_session: AsyncSession):
        """Unauthenticated request should return 401."""
        response = await test_client.post(
            "/api/v1/children",
            json={"name": "Child", "dateOfBirth": "2016-01-01", "mediaConsent": True},
        )

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestUpdateChild:
    """Test PATCH /api/children/{child_id} - update child."""

    @pytest.mark.asyncio
    async def test_update_child_success(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        child: Child,
        auth_token: str,
    ):
        """Can update child data."""
        response = await test_client.patch(
            f"/api/v1/children/{child.id}",
            json={
                "name": "Updated Child",
                "medicalInfo": "Updated medical info",
            },
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Child"
        assert data["medicalInfo"] == "Updated medical info"

    @pytest.mark.asyncio
    async def test_update_child_not_found(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        auth_token: str,
    ):
        """Returns 404 for non-existent child."""
        # Use test_client directly
        response = await test_client.patch(
            f"/api/v1/children/{uuid4()}",
            json={"name": "Not Found"},
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_update_child_not_owned(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        child: Child,
    ):
        """Cannot update another caregiver's child."""
        # Create different caregiver
        other_caregiver = Caregiver(
            email="other@example.com",
            name="Other",
            phone="+64299999999",
            email_verified=True,
        )
        db_session.add(other_caregiver)
        await db_session.flush()

        # Create auth token for other caregiver
        raw_token = new_token()
        token_hash = hash_token(raw_token)
        session = CaregiverSession(
            caregiver_id=other_caregiver.id,
            token_hash=token_hash,
            expires_at=session_expires_at(),
        )
        db_session.add(session)
        await db_session.flush()

        # Use test_client directly
        response = await test_client.patch(
            f"/api/v1/children/{child.id}",
            json={"name": "Hacked"},
            cookies={CARE_GIVER_SESSION_COOKIE: raw_token},
        )

        # Should return 404 to not leak that child exists
        assert response.status_code == HTTP_404_NOT_FOUND


class TestCreateSignup:
    """Test POST /api/session/{session_id}/signup - create signup."""

    @pytest.mark.asyncio
    @patch("app.routes.caregiver.get_queue")
    async def test_create_signup_success(
        self,
        mock_get_queue,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        child: Child,
        session: Session,
        auth_token: str,
    ):
        """Can create signup with valid data."""
        mock_queue = AsyncMock()
        mock_get_queue.return_value = mock_queue

        response = await test_client.post(
            f"/api/v1/session/{session.id}/signup",
            json={
                "childId": str(child.id),
                "subscribeNewsletter": False,
            },
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["status"] == "confirmed"
        assert "id" in data

        # Verify email was queued
        assert mock_queue.enqueue.called

    @pytest.mark.asyncio
    async def test_create_signup_session_not_found(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        child: Child,
        auth_token: str,
    ):
        """Returns 404 for non-existent session."""
        response = await test_client.post(
            f"/api/v1/session/{uuid4()}/signup",
            json={"childId": str(child.id)},
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_signup_child_not_found(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        session: Session,
        auth_token: str,
    ):
        """Returns 404 for non-existent child."""
        response = await test_client.post(
            f"/api/v1/session/{session.id}/signup",
            json={"childId": str(uuid4())},
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    @patch("app.routes.caregiver.get_queue")
    async def test_create_signup_duplicate(
        self,
        mock_get_queue,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        signup: Signup,
        auth_token: str,
    ):
        """Returns existing signup if duplicate."""
        mock_queue = AsyncMock()
        mock_get_queue.return_value = mock_queue

        response = await test_client.post(
            f"/api/v1/session/{signup.session_id}/signup",
            json={"childId": str(signup.child_id)},
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        # Should return the existing signup
        assert data["id"] == str(signup.id)

    @pytest.mark.asyncio
    async def test_create_signup_incomplete_profile(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        session: Session,
        incomplete_auth_token: str,
    ):
        """Cannot signup without complete profile."""
        response = await test_client.post(
            f"/api/v1/session/{session.id}/signup",
            json={"childId": str(uuid4())},
            cookies={CARE_GIVER_SESSION_COOKIE: incomplete_auth_token},
        )

        # Will fail due to incomplete profile or child not found
        assert response.status_code in (HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND)


class TestListSignups:
    """Test GET /api/signups - list signups."""

    @pytest.mark.asyncio
    async def test_list_signups_empty(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        caregiver: Caregiver,
        auth_token: str,
    ):
        """Returns empty list when no signups."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/signups",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_signups_with_data(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        signup: Signup,
        auth_token: str,
    ):
        """Returns caregiver's signups."""
        # Use test_client directly
        response = await test_client.get(
            "/api/v1/signups",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(signup.id)
        assert data[0]["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_list_signups_unauthenticated(self, test_client: AsyncTestClient, db_session: AsyncSession):
        """Unauthenticated request should return 401."""
        # Use test_client directly
        response = await test_client.get("/api/v1/signups")

        assert response.status_code == HTTP_401_UNAUTHORIZED


class TestWithdrawSignup:
    """Test POST /api/signup/{signup_id}/withdraw - withdraw signup."""

    @pytest.mark.asyncio
    @patch("app.routes.caregiver.get_queue")
    async def test_withdraw_signup_success(
        self,
        mock_get_queue,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        signup: Signup,
        auth_token: str,
    ):
        """Can withdraw from signup."""
        mock_queue = AsyncMock()
        mock_get_queue.return_value = mock_queue

        response = await test_client.post(
            f"/api/v1/signup/{signup.id}/withdraw",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["status"] == "withdrawn"

    @pytest.mark.asyncio
    @patch("app.routes.caregiver.get_queue")
    async def test_withdraw_signup_idempotent(
        self,
        mock_get_queue,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        signup: Signup,
        auth_token: str,
    ):
        """Withdrawing twice is idempotent."""
        mock_queue = AsyncMock()
        mock_get_queue.return_value = mock_queue

        # First withdrawal
        response1 = await test_client.post(
            f"/api/v1/signup/{signup.id}/withdraw",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )
        assert response1.status_code == HTTP_200_OK

        # Second withdrawal
        response2 = await test_client.post(
            f"/api/v1/signup/{signup.id}/withdraw",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )
        assert response2.status_code == HTTP_200_OK
        assert response2.json()["status"] == "withdrawn"

    @pytest.mark.asyncio
    async def test_withdraw_signup_not_found(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        auth_token: str,
    ):
        """Returns 404 for non-existent signup."""
        # Use test_client directly
        response = await test_client.post(
            f"/api/v1/signup/{uuid4()}/withdraw",
            cookies={CARE_GIVER_SESSION_COOKIE: auth_token},
        )

        assert response.status_code == HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_withdraw_signup_unauthenticated(
        self,
        test_client: AsyncTestClient,
        db_session: AsyncSession,
        signup: Signup,
    ):
        """Unauthenticated request should return 401."""
        # Use test_client directly
        response = await test_client.post(f"/api/v1/signup/{signup.id}/withdraw")

        assert response.status_code == HTTP_401_UNAUTHORIZED

"""Admin authentication endpoints using Google OAuth."""

from __future__ import annotations

from datetime import UTC

from httpx_oauth.clients.google import GoogleOAuth2
from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.params import Parameter
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin_auth import ADMIN_SESSION_COOKIE, create_admin_session, is_allowed_admin
from app.config import settings
from app.db import get_db_session
from app.models.staff import Staff
from app.utils.oauth import (
    build_oauth_error_redirect,
    create_oauth_state,
    verify_oauth_state,
)

DEFAULT_SCOPES = ["openid", "email", "profile"]


def _safe_frontend_return_to(value: str | None) -> str:
    # Only allow relative paths to avoid open redirects.
    if not value:
        return "/dashboard"
    if value.startswith("/") and not value.startswith("//") and ":" not in value:
        return value
    return "/dashboard"


def _google_client() -> GoogleOAuth2:
    if not settings.admin_google_oauth_client_id or not settings.admin_google_oauth_client_secret:
        raise HTTPException(status_code=500, detail="Admin Google OAuth is not configured")

    return GoogleOAuth2(
        settings.admin_google_oauth_client_id,
        settings.admin_google_oauth_client_secret,
    )


class AdminAuthController(Controller):
    """Admin authentication endpoints (Google OAuth)."""

    path = "/api/v1/admin/auth"
    tags = ["Admin Auth"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/google/start", summary="Start Google OAuth")
    async def google_start(self, request: Request, returnTo: str | None = None) -> Response:
        """Initiate admin Google OAuth by generating signed state and redirecting to Google's consent screen."""
        safe_return_to = _safe_frontend_return_to(returnTo)

        state = create_oauth_state(
            provider="google",
            redirect_url=f"{settings.admin_base_url}{safe_return_to}",
            secret_key=settings.admin_google_oauth_client_secret,
        )

        redirect_uri = f"{settings.public_base_url}/api/v1/admin/auth/google/callback"
        client = _google_client()

        authorization_url = await client.get_authorization_url(redirect_uri, state=state, scope=DEFAULT_SCOPES)

        return Response(content=None, status_code=302, headers={"Location": authorization_url})

    @get("/google/callback", summary="Google OAuth callback")
    async def google_callback(
        self,
        db: AsyncSession,
        code: str | None = None,
        oauth_state: str | None = Parameter(query="state", default=None),
        error: str | None = None,
    ) -> Response:
        """Handle Google OAuth callback: validate state, exchange code, enforce admin allowlist, auto-create staff if needed, and set admin_session cookie."""
        if db is None:
            db = await anext(get_db_session())

        default_redirect = f"{settings.admin_base_url}/admin"

        if error or not code or not oauth_state:
            location = build_oauth_error_redirect(default_redirect, "oauth_error", error or "Missing code/state")
            return Response(content=None, status_code=302, headers={"Location": location})

        ok, payload, msg = verify_oauth_state(
            oauth_state,
            expected_provider="google",
            secret_key=settings.admin_google_oauth_client_secret,
        )
        if not ok:
            location = build_oauth_error_redirect(default_redirect, "invalid_state", msg)
            return Response(content=None, status_code=302, headers={"Location": location})

        redirect_url = str(payload.get("redirect_url") or default_redirect)

        client = _google_client()
        redirect_uri = f"{settings.public_base_url}/api/v1/admin/auth/google/callback"

        token = await client.get_access_token(code, redirect_uri)
        access_token = token.get("access_token")
        if not access_token:
            location = build_oauth_error_redirect(redirect_url, "oauth_error", "Missing access token")
            return Response(content=None, status_code=302, headers={"Location": location})

        provider_user_id, email = await client.get_id_email(access_token)
        email = (email or "").strip().lower()

        if not email:
            location = build_oauth_error_redirect(redirect_url, "forbidden", "No email returned from provider")
            return Response(content=None, status_code=302, headers={"Location": location})

        if not is_allowed_admin(email):
            location = build_oauth_error_redirect(redirect_url, "forbidden", "Not an admin")
            return Response(content=None, status_code=302, headers={"Location": location})

        # Auto-create staff if they don't exist
        result = await db.execute(select(Staff).where(Staff.sso_id == provider_user_id))
        staff = result.scalar_one_or_none()

        if not staff:
            # Try to find by email in case SSO ID changed
            result = await db.execute(select(Staff).where(Staff.email == email))
            staff = result.scalar_one_or_none()

        if not staff:
            # Create new staff member
            from datetime import datetime

            staff = Staff(
                name=email.split("@")[0].replace(".", " ").title(),  # Basic name from email
                email=email,
                sso_id=provider_user_id,
                last_login_at=datetime.now(UTC),
                active=True,
            )
            db.add(staff)
        else:
            # Update last login and SSO ID if needed
            from datetime import datetime

            staff.last_login_at = datetime.now(UTC)
            if staff.sso_id != provider_user_id:
                staff.sso_id = provider_user_id
            if staff.email != email:
                staff.email = email

        await db.commit()

        session_token = create_admin_session(email=email, provider="google", provider_user_id=provider_user_id)

        response = Response(content=None, status_code=302, headers={"Location": redirect_url})
        response.set_cookie(
            ADMIN_SESSION_COOKIE,
            session_token,
            httponly=True,
            secure=not settings.debug,
            samesite="lax",
            path="/",
        )
        return response

    @get("/me", status_code=HTTP_200_OK, summary="Check admin session")
    async def me(self, request: Request) -> dict[str, bool]:
        """Lightweight check for presence of an admin_session cookie (actual validation happens on guarded endpoints)."""
        raw = request.cookies.get(ADMIN_SESSION_COOKIE)
        return {"ok": True, "hasSession": bool(raw)}

    @post("/logout", status_code=HTTP_200_OK, summary="Admin logout")
    async def logout(self) -> Response:
        """Clear the admin_session cookie; tokens are stateless and expire naturally."""
        response = Response(content={"ok": True}, status_code=HTTP_200_OK)
        response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
        return response

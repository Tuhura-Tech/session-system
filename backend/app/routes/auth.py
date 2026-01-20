from __future__ import annotations

import logging
from urllib.parse import quote, urlparse

from litestar import Controller, Request, get, post
from litestar.di import Provide
from litestar.response import Response
from litestar.status_codes import HTTP_200_OK
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    CARE_GIVER_SESSION_COOKIE,
    hash_token,
    magic_link_expires_at,
    new_token,
    session_expires_at,
    utcnow,
)
from app.config import settings
from app.db import get_db_session
from app.models.caregiver import Caregiver
from app.models.caregiver_auth import CaregiverMagicLink, CaregiverSession
from app.schemas.auth import LogoutResponse, MagicLinkRequest, MagicLinkRequestResponse
from app.services.email import email_service

logger = logging.getLogger(__name__)


def _safe_return_to(value: str | None) -> str:
    # Only allow relative paths to avoid open redirects.
    if not value:
        return "/account"
    if value.startswith("/") and not value.startswith("//") and ":" not in value:
        return value
    return "/account"


class AuthController(Controller):
    """Caregiver authentication endpoints (magic-link)."""

    path = "/api/v1/auth"
    tags = ["Auth"]
    dependencies = {"db": Provide(get_db_session)}

    @post("/magic-link", status_code=HTTP_200_OK, summary="Request magic link")
    async def request_magic_link(self, db: AsyncSession, data: MagicLinkRequest) -> MagicLinkRequestResponse:
        """Send a passwordless magic link to a caregiver email, creating an account if needed and reusing unexpired links to throttle."""
        print("Requesting magic link for email:", data.email)
        email = str(data.email).strip().lower()
        return_to = _safe_return_to(data.return_to)

        # Find or create caregiver account.
        caregiver_result = await db.execute(select(Caregiver).where(Caregiver.email == email))
        caregiver = caregiver_result.scalar_one_or_none()
        if not caregiver:
            caregiver = Caregiver(email=email)
            db.add(caregiver)
            await db.flush()

        # Throttle: re-use a recent, unexpired unused link if one exists.
        now = utcnow()
        existing_result = await db.execute(
            select(CaregiverMagicLink)
            .where(CaregiverMagicLink.caregiver_id == caregiver.id)
            .where(CaregiverMagicLink.used_at.is_(None))
            .where(CaregiverMagicLink.expires_at > now)
            .order_by(desc(CaregiverMagicLink.created_at))
            .limit(1)
        )
        existing = existing_result.scalar_one_or_none()

        raw_token = new_token()
        token_hash = hash_token(raw_token)

        if existing:
            # Keep behavior consistent: always send an email, but don't create many rows.
            token_hash = existing.token_hash
            raw_token = None  # Can't reconstruct; create a new row instead.

        if raw_token is None:
            raw_token = new_token()
            token_hash = hash_token(raw_token)

        magic_link = CaregiverMagicLink(
            caregiver_id=caregiver.id,
            token_hash=token_hash,
            expires_at=magic_link_expires_at(),
        )
        db.add(magic_link)
        await db.flush()

        consume_url = (
            f"{settings.public_base_url}/api/v1/auth/magic-link/consume"
            f"?token={quote(raw_token)}&returnTo={quote(return_to)}"
        )

        await email_service.send_magic_link_login(
            to_email=email,
            magic_link_url=consume_url,
            caregiver_name=caregiver.name,
            ttl_minutes=settings.magic_link_ttl_minutes,
        )

        debug_token = raw_token if settings.debug else None
        return MagicLinkRequestResponse(ok=True, debugToken=debug_token)

    @get("/magic-link/consume", summary="Consume magic link")
    async def consume_magic_link(self, db: AsyncSession, token: str, returnTo: str | None = None) -> Response:
        """Consume a magic link, mark it used, set the caregiver session cookie, and redirect with safe return handling."""
        safe_return_to = _safe_return_to(returnTo)
        token_hash = hash_token(token)
        now = utcnow()

        result = await db.execute(
            select(CaregiverMagicLink)
            .where(CaregiverMagicLink.token_hash == token_hash)
            .where(CaregiverMagicLink.used_at.is_(None))
            .where(CaregiverMagicLink.expires_at > now)
        )
        link = result.scalar_one_or_none()

        if not link:
            return Response(
                content={"ok": False, "error": "Invalid or expired link"},
                status_code=400,
            )

        caregiver = await db.get(Caregiver, link.caregiver_id)
        if not caregiver:
            return Response(content={"ok": False, "error": "Invalid link"}, status_code=400)

        # Mark link used.
        link.used_at = now
        caregiver.email_verified = True
        caregiver.last_login_at = now

        # Create session.
        raw_session_token = new_token()
        session = CaregiverSession(
            caregiver_id=caregiver.id,
            token_hash=hash_token(raw_session_token),
            expires_at=session_expires_at(),
        )
        db.add(session)
        await db.flush()

        # Redirect back to the frontend.
        location = f"{settings.frontend_base_url}{safe_return_to}"
        response = Response(content=None, status_code=302, headers={"Location": location})

        parsed = urlparse(settings.frontend_base_url)
        frontend_host = parsed.hostname or "localhost"

        etld_min_parts = 2

        def _cookie_domain(host: str) -> str | None:
            if host in {"localhost", "127.0.0.1"}:
                return None
            parts = host.split(".")
            if len(parts) >= etld_min_parts:
                # Use eTLD+1 style domain so cookie is valid on both api and frontend
                return "." + ".".join(parts[-2:])
            return host

        cookie_domain = _cookie_domain(frontend_host)
        cookie_secure = parsed.scheme == "https"

        response.set_cookie(
            CARE_GIVER_SESSION_COOKIE,
            raw_session_token,
            domain=cookie_domain,
            httponly=True,
            secure=cookie_secure,
            samesite="none" if cookie_domain else "lax",
            path="/",
        )

        return response

    @post("/logout", status_code=HTTP_200_OK, summary="Log out")
    async def logout(self, request: Request, db: AsyncSession) -> Response:
        """Revoke the caregiver session if present and clear the session cookie (idempotent)."""
        raw = request.cookies.get(CARE_GIVER_SESSION_COOKIE)
        if raw:
            token_hash = hash_token(raw)
            now = utcnow()
            result = await db.execute(select(CaregiverSession).where(CaregiverSession.token_hash == token_hash))
            sess = result.scalar_one_or_none()
            if sess and sess.revoked_at is None:
                sess.revoked_at = now

        response = Response(content=LogoutResponse(ok=True).model_dump(), status_code=HTTP_200_OK)
        response.delete_cookie(CARE_GIVER_SESSION_COOKIE, path="/")
        return response

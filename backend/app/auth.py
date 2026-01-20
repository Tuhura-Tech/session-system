from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from litestar.connection import Request
from litestar.exceptions import NotAuthorizedException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.caregiver import Caregiver
from app.models.caregiver_auth import CaregiverSession

CARE_GIVER_SESSION_COOKIE = "caregiver_session"


def _hash_token(token: str) -> str:
    # Stable hash for DB lookup; includes server-side secret to mitigate token DB leakage.
    h = hashlib.sha256()
    h.update(settings.auth_secret.encode("utf-8"))
    h.update(b"|")
    h.update(token.encode("utf-8"))
    return h.hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def utcnow() -> datetime:
    return datetime.now(UTC)


def magic_link_expires_at() -> datetime:
    return utcnow() + timedelta(minutes=settings.magic_link_ttl_minutes)


def session_expires_at() -> datetime:
    return utcnow() + timedelta(days=settings.caregiver_session_ttl_days)


async def get_current_caregiver(request: Request, db: AsyncSession, *, required: bool = True) -> Caregiver | None:
    raw = request.cookies.get(CARE_GIVER_SESSION_COOKIE)
    if not raw:
        if required:
            raise NotAuthorizedException(detail="Not signed in")
        return None

    token_hash = _hash_token(raw)
    now = utcnow()

    result = await db.execute(
        select(CaregiverSession)
        .where(CaregiverSession.token_hash == token_hash)
        .where(CaregiverSession.revoked_at.is_(None))
        .where(CaregiverSession.expires_at > now)
    )
    session = result.scalar_one_or_none()
    if not session:
        if required:
            raise NotAuthorizedException(detail="Session expired")
        return None

    caregiver = await db.get(Caregiver, session.caregiver_id)
    if not caregiver:
        if required:
            raise NotAuthorizedException(detail="Invalid session")
        return None

    return caregiver


def hash_token(token: str) -> str:
    return _hash_token(token)

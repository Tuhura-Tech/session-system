"""Newsletter integration.

System requirement SR15: If subscribeNewsletter=true on signup, notify Ghost (or equivalent).

This implementation uses a configurable webhook URL. If not configured, it becomes a no-op.
"""

from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def notify_newsletter_subscription(*, email: str, name: str | None = None) -> None:
    """Notify an external newsletter system about an opt-in.

    If `settings.newsletter_webhook_url` is not configured, this function is a no-op.
    """
    url = (settings.newsletter_webhook_url or "").strip()
    if not url:
        logger.info("Newsletter webhook not configured; skipping opt-in for %s", email)
        return

    payload = {
        "members": [
            {
                "name": name,
                "email": email,
                "labels": [{"name": "Session", "slug": "session"}],
            }
        ]
    }
    if name:
        payload["name"] = name

    headers: dict[str, str] = {"Content-Type": "application/json"}
    token = (settings.newsletter_webhook_token or "").strip()
    if token:
        headers["Authorization"] = f"Ghost {token}"

    if settings.email_dry_run:
        logger.info("DRY RUN - Would POST newsletter opt-in to %s: %s", url, payload)
        return

    async with httpx.AsyncClient(timeout=10.0) as client:
        path = f"{url}/ghost/api/admin/members/"
        resp = await client.post(path, json=payload, headers=headers)
        resp.raise_for_status()

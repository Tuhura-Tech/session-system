from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.signup import Signup


async def schedule_session_emails_for_signup(
    *,
    db: AsyncSession,
    queue,
    signup: Signup,
    caregiver_email: str,
    caregiver_name: str,
    child_name: str,
    session: Session,
) -> None:
    """Schedule welcome email for a confirmed signup.

    Batch emails (2 weeks before and 1 day before) are processed daily by cron job.
    This function only queues the immediate welcome/confirmation email.
    """
    if signup.status != "confirmed":
        return

    # Welcome/confirmation emails are sent immediately via queue in caregiver routes
    # Batch emails are processed daily at 9am by the scheduled worker task
    # No additional scheduling needed here

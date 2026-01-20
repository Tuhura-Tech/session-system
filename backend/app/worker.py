"""SAQ worker for background task processing."""

import asyncio
import logging
from datetime import datetime
from typing import Any

from saq import CronJob, Queue
from saq.types import Context

from app.config import settings
from app.services.email import email_service
from app.services.newsletter import notify_newsletter_subscription

logger = logging.getLogger(__name__)


def _build_bcc(to_email: str, contact_email: str | None = None, bcc_emails: list[str] | None = None) -> list[str]:
    # Keep recipients private; de-dupe while preserving order.
    return list(dict.fromkeys([to_email] + ([contact_email] if contact_email else []) + (bcc_emails or [])))


async def send_signup_confirmation_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    term_summary: str | None = None,
    what_to_bring: str | None = None,
    signup_status: str,
    signup_id: str,
    session_id: str,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Background task to send signup confirmation email.

    This is queued when a caregiver signs up for a session.
    """
    logger.info(f"Sending signup confirmation to {to_email} for signup {signup_id}")

    success = await email_service.send_signup_confirmation(
        to_email=to_email,
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue,
        session_address=session_address,
        session_time=session_time,
        term_summary=term_summary,
        what_to_bring=what_to_bring,
        signup_status=signup_status,
        signup_id=signup_id,
        session_id=session_id,
        bcc_emails=bcc_emails,
    )

    return {
        "success": success,
        "to_email": to_email,
        "signup_id": signup_id,
        "sent_at": datetime.now().isoformat(),
    }


async def send_session_reminder_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    session_date: str | None = None,
    what_to_bring: str | None = None,
    contact_email: str | None = None,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Background task to send session reminder email (1 day before).

    Batch email: all caregivers BCC'd, staff and session contact also BCC'd.
    """
    logger.info(f"Sending session reminder to {to_email}")

    html, text = email_service.render_template(
        "session_reminder",
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue or session_name,
        session_address=session_address,
        session_time=session_time,
        session_date=session_date,
        what_to_bring=[what_to_bring] if what_to_bring else [],
        contact_email=contact_email or settings.email_contact,
    )

    from app.services.email import EmailMessage

    # 1-day notice is a batch email: org email in To, all recipients BCC'd
    all_bcc = _build_bcc(to_email, contact_email, bcc_emails)

    message = EmailMessage(
        to=[settings.email_contact],
        subject=f"Reminder: {child_name}'s session tomorrow - {session_name}",
        html=html,
        text=text,
        bcc=all_bcc,
        reply_to=settings.email_contact,
    )

    success = await email_service.send(message)

    return {
        "success": success,
        "to_email": to_email,
        "sent_at": datetime.now().isoformat(),
    }


async def send_session_term_info_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    first_session_date: str,
    calendar_url: str,
    term_summary: str | None = None,
    what_to_bring: str | None = None,
    contact_email: str | None = None,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Background task to send session term info email (2 weeks before).

    Batch email: org email in To, all caregivers + staff + session contact BCC'd.
    """
    logger.info(f"Sending session term info to {to_email}")

    html, text = email_service.render_template(
        "session_term_info",
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue or session_name,
        session_address=session_address,
        session_time=session_time,
        first_session_date=first_session_date,
        calendar_url=calendar_url,
        term_summary=term_summary,
        what_to_bring=what_to_bring,
        contact_email=contact_email or settings.email_contact,
    )

    from app.services.email import EmailMessage

    # 2-week notice is a batch email: org email in To, all recipients BCC'd
    all_bcc = _build_bcc(to_email, contact_email, bcc_emails)

    message = EmailMessage(
        to=[settings.email_contact],
        subject=f"Session details: {child_name} - {session_name}",
        html=html,
        text=text,
        bcc=all_bcc,
        reply_to=contact_email or settings.email_contact,
    )

    success = await email_service.send(message)

    return {
        "success": success,
        "to_email": to_email,
        "sent_at": datetime.now().isoformat(),
    }


async def send_waitlist_confirmed_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    first_session_date: str | None = None,
    calendar_url: str | None = None,
    what_to_bring: str | None = None,
    contact_email: str | None = None,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Send an email when a waitlisted signup is moved to confirmed (direct to caregiver)."""
    logger.info(f"Sending waitlist confirmed email to {to_email}")

    html, text = email_service.render_template(
        "waitlist_confirmed",
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue or session_name,
        session_address=session_address,
        session_time=session_time,
        first_session_date=first_session_date,
        calendar_url=calendar_url,
        what_to_bring=what_to_bring,
        contact_email=contact_email or settings.email_contact,
    )

    from app.services.email import EmailMessage

    message = EmailMessage(
        to=[to_email],
        subject=f"Spot confirmed: {child_name} - {session_name}",
        html=html,
        text=text,
        reply_to=settings.email_contact,
    )

    success = await email_service.send(message)
    return {
        "success": success,
        "to_email": to_email,
        "sent_at": datetime.now().isoformat(),
    }


async def send_session_change_alert_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    update_title: str,
    update_message: str | None = None,
    affected_date: str | None = None,
    contact_email: str | None = None,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Send an email for cancellations/venue changes/time changes (direct to caregiver).

    Triggered by admin functionality.
    """
    logger.info(f"Sending session change alert to {to_email}")

    html, text = email_service.render_template(
        "session_change_alert",
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue or session_name,
        session_address=session_address,
        session_time=session_time,
        update_title=update_title,
        update_message=update_message,
        affected_date=affected_date,
        contact_email=contact_email or settings.email_contact,
    )

    from app.services.email import EmailMessage

    message = EmailMessage(
        to=[to_email],
        subject=f"Update: {session_name} - {child_name}",
        html=html,
        text=text,
        reply_to=settings.email_contact,
    )

    success = await email_service.send(message)
    return {
        "success": success,
        "to_email": to_email,
        "sent_at": datetime.now().isoformat(),
    }


async def send_missed_session_followup_task(
    ctx: Context,
    *,
    to_email: str,
    caregiver_name: str,
    child_name: str,
    session_name: str,
    session_venue: str | None,
    session_address: str,
    session_time: str,
    missed_date: str | None = None,
    next_session_date: str | None = None,
    contact_email: str | None = None,
    bcc_emails: list[str] | None = None,
) -> dict[str, Any]:
    """Send a follow-up email when a child misses a session (direct to caregiver).

    Triggered by admin functionality once attendance/no-show tracking exists.
    """
    logger.info(f"Sending missed-session followup to {to_email}")

    html, text = email_service.render_template(
        "session_missed_followup",
        caregiver_name=caregiver_name,
        child_name=child_name,
        session_name=session_name,
        session_venue=session_venue or session_name,
        session_address=session_address,
        session_time=session_time,
        missed_date=missed_date,
        next_session_date=next_session_date,
        contact_email=contact_email or settings.email_contact,
    )

    from app.services.email import EmailMessage

    message = EmailMessage(
        to=[to_email],
        subject=f"We missed you: {child_name} - {session_name}",
        html=html,
        text=text,
        reply_to=settings.email_contact,
    )

    success = await email_service.send(message)
    return {
        "success": success,
        "to_email": to_email,
        "sent_at": datetime.now().isoformat(),
    }


async def notify_newsletter_subscription_task(
    ctx: Context,
    *,
    email: str,
    name: str | None = None,
) -> dict[str, Any]:
    """Notify newsletter system about an opt-in.

    Retries are bounded with a small backoff to improve reliability of external calls.
    """
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            await notify_newsletter_subscription(email=email, name=name)
            return {
                "success": True,
                "email": email,
                "sent_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(
                "Newsletter webhook failed (attempt %s/%s) for %s: %s",
                attempt,
                max_attempts,
                email,
                e,
            )
            if attempt < max_attempts:
                await asyncio.sleep(0.5 * (2 ** (attempt - 1)))

    return {"success": False, "email": email, "sent_at": datetime.now().isoformat()}


async def process_batch_emails_task(ctx: Context) -> dict[str, Any]:
    """Cron job that runs daily at 9am to send batch emails.

    Checks database for:
    - Signups that are 2 weeks before their first session (send 2-week notice)
    - Signups that are 1 day before their first session (send 1-day reminder)

    Emails are sent as batch emails with org email in To and all recipients BCC'd.
    """
    from datetime import datetime, time, timedelta
    from zoneinfo import ZoneInfo

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import selectinload

    from app.models.session import Session
    from app.models.session_block import SessionBlock
    from app.models.session_block_link import SessionBlockLink
    from app.models.session_occurrence import SessionOccurrence
    from app.models.signup import Signup
    from app.schemas.session import _format_time_range
    from app.services.email import EmailMessage

    logger.info("Processing batch emails at 9am")

    tz = ZoneInfo("Pacific/Auckland")
    now_local = datetime.now(tz)
    today_local = now_local.date()

    # Get database session
    db = AsyncSession()
    try:
        # Find all confirmed signups
        signups_result = await db.execute(
            select(Signup)
            .where(Signup.status == "confirmed")
            .options(
                selectinload(Signup.session).selectinload(Session.session_location),
                selectinload(Signup.caregiver),
                selectinload(Signup.child),
            )
        )
        signups = signups_result.scalars().all()

        emails_to_send = []  # List of (email_type, email_data) tuples

        for signup in signups:
            session = signup.session
            caregiver = signup.caregiver
            child = signup.child
            loc = session.session_location if hasattr(session, "session_location") else None

            if not loc:
                continue

            session_venue = loc.name if loc else session.name
            session_address = loc.address if loc else ""
            session_contact_email = loc.contact_email if loc else None
            session_time = _format_time_range(session.day_of_week, session.start_time, session.end_time)

            # Determine first session date
            first_start_local = None
            block_label = None

            session_type = getattr(session, "session_type", "term")

            if session_type == "special":
                # For special sessions, use first non-cancelled occurrence
                first_occ_result = await db.execute(
                    select(SessionOccurrence)
                    .where(
                        SessionOccurrence.session_id == session.id,
                        SessionOccurrence.cancelled.is_(False),
                    )
                    .order_by(SessionOccurrence.starts_at.asc())
                    .limit(1)
                )
                first_occ = first_occ_result.scalar_one_or_none()
                if first_occ and first_occ.starts_at:
                    first_start_local = first_occ.starts_at.astimezone(tz)
            else:
                # For term sessions, find first occurrence in earliest block
                blocks_result = await db.execute(
                    select(SessionBlock)
                    .join(SessionBlockLink, SessionBlockLink.block_id == SessionBlock.id)
                    .where(SessionBlockLink.session_id == session.id)
                    .order_by(SessionBlock.year.asc(), SessionBlock.start_date.asc())
                    .limit(1)
                )
                block = blocks_result.scalar_one_or_none()

                if block:
                    block_label = block.name
                    block_start_local = datetime.combine(block.start_date, time(hour=0), tzinfo=tz)

                    # Find first occurrence in this block
                    occ_result = await db.execute(
                        select(SessionOccurrence)
                        .where(
                            SessionOccurrence.session_id == session.id,
                            SessionOccurrence.cancelled.is_(False),
                            SessionOccurrence.block_id == block.id,
                            SessionOccurrence.starts_at >= block_start_local,
                        )
                        .order_by(SessionOccurrence.starts_at.asc())
                        .limit(1)
                    )
                    occ = occ_result.scalar_one_or_none()

                    if occ and occ.starts_at:
                        first_start_local = occ.starts_at.astimezone(tz)
                    # Calculate based on day of week
                    elif session.day_of_week is not None and session.start_time is not None:
                        days_ahead = (int(session.day_of_week) - block_start_local.weekday() + 7) % 7
                        first_date = block_start_local.date() + timedelta(days=days_ahead)
                        first_start_local = datetime.combine(first_date, session.start_time, tzinfo=tz)

            if not first_start_local:
                continue

            first_session_date = first_start_local.strftime("%a %d %b %Y, %-I:%M%p")
            calendar_url = f"{settings.public_base_url}/api/v1/session/{session.id}/calendar.ics"

            # Check if today is 2 weeks before first session
            two_weeks_before = (first_start_local - timedelta(days=14)).date()
            if today_local == two_weeks_before:
                emails_to_send.append(
                    (
                        "term_info",
                        {
                            "caregiver_email": caregiver.email,
                            "caregiver_name": caregiver.name,
                            "child_name": child.name,
                            "session_name": session.name,
                            "session_venue": session_venue,
                            "session_address": session_address,
                            "session_time": session_time,
                            "first_session_date": first_session_date,
                            "calendar_url": calendar_url,
                            "term_summary": block_label,
                            "what_to_bring": session.what_to_bring,
                            "contact_email": session_contact_email,
                        },
                    )
                )

            # Check if today is 1 day before first session
            one_day_before = (first_start_local - timedelta(days=1)).date()
            if today_local == one_day_before:
                emails_to_send.append(
                    (
                        "reminder",
                        {
                            "caregiver_email": caregiver.email,
                            "caregiver_name": caregiver.name,
                            "child_name": child.name,
                            "session_name": session.name,
                            "session_venue": session_venue,
                            "session_address": session_address,
                            "session_time": session_time,
                            "session_date": first_session_date,
                            "what_to_bring": session.what_to_bring,
                            "contact_email": session_contact_email,
                        },
                    )
                )

        # Group emails by type and send batch emails
        term_info_emails = [e for t, e in emails_to_send if t == "term_info"]
        reminder_emails = [e for t, e in emails_to_send if t == "reminder"]

        sent_count = 0

        # Send 2-week notice as batch
        if term_info_emails:
            logger.info(f"Sending {len(term_info_emails)} 2-week notice emails")
            for email_data in term_info_emails:
                html, text = email_service.render_template(
                    "session_term_info",
                    caregiver_name=email_data["caregiver_name"],
                    child_name=email_data["child_name"],
                    session_name=email_data["session_name"],
                    session_venue=email_data["session_venue"],
                    session_address=email_data["session_address"],
                    session_time=email_data["session_time"],
                    first_session_date=email_data["first_session_date"],
                    calendar_url=email_data["calendar_url"],
                    term_summary=email_data["term_summary"],
                    what_to_bring=email_data["what_to_bring"],
                    contact_email=email_data["contact_email"] or settings.email_contact,
                )

                bcc_recipients = [
                    email_data["caregiver_email"],
                ]
                if email_data["contact_email"]:
                    bcc_recipients.append(email_data["contact_email"])

                message = EmailMessage(
                    to=[settings.email_contact],
                    subject=f"Session details: {email_data['child_name']} - {email_data['session_name']}",
                    html=html,
                    text=text,
                    bcc=bcc_recipients,
                    reply_to=email_data["contact_email"] or settings.email_contact,
                )

                if await email_service.send(message):
                    sent_count += 1

        # Send 1-day reminder as batch
        if reminder_emails:
            logger.info(f"Sending {len(reminder_emails)} 1-day reminder emails")
            for email_data in reminder_emails:
                html, text = email_service.render_template(
                    "session_reminder",
                    caregiver_name=email_data["caregiver_name"],
                    child_name=email_data["child_name"],
                    session_name=email_data["session_name"],
                    session_venue=email_data["session_venue"],
                    session_address=email_data["session_address"],
                    session_time=email_data["session_time"],
                    session_date=email_data["session_date"],
                    what_to_bring=[email_data["what_to_bring"]] if email_data["what_to_bring"] else [],
                    contact_email=email_data["contact_email"] or settings.email_contact,
                )

                bcc_recipients = [
                    email_data["caregiver_email"],
                ]
                if email_data["contact_email"]:
                    bcc_recipients.append(email_data["contact_email"])

                message = EmailMessage(
                    to=[settings.email_contact],
                    subject=f"Reminder: {email_data['child_name']}'s session tomorrow - {email_data['session_name']}",
                    html=html,
                    text=text,
                    bcc=bcc_recipients,
                    reply_to=email_data["contact_email"] or settings.email_contact,
                )

                if await email_service.send(message):
                    sent_count += 1

        return {
            "success": True,
            "emails_sent": sent_count,
            "processed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error processing batch emails: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "processed_at": datetime.now().isoformat(),
        }
    finally:
        await db.close()


# Queue settings
queue_settings = {
    "queue": Queue.from_url(settings.redis_url),
    "functions": [
        send_signup_confirmation_task,
        send_session_reminder_task,
        send_session_term_info_task,
        send_waitlist_confirmed_task,
        send_session_change_alert_task,
        send_missed_session_followup_task,
        notify_newsletter_subscription_task,
        process_batch_emails_task,
    ],
    "concurrency": 10,
    "cron_jobs": [
        # Run batch email processing daily at 9:00 AM Pacific/Auckland time
        CronJob(process_batch_emails_task, cron="0 9 * * *"),
    ],
}


def get_queue() -> "Queue[Any]":
    """Get the SAQ queue instance."""
    return queue_settings["queue"]

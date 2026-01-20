"""Email service using Mailgun API with Jinja2 templating."""

import logging
from dataclasses import dataclass
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings

logger = logging.getLogger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"


@dataclass
class EmailMessage:
    """An email message to be sent."""

    to: list[str]
    subject: str
    html: str
    text: str | None = None
    bcc: list[str] | None = None
    reply_to: str | None = None


class EmailService:
    """Service for sending emails via Mailgun."""

    def __init__(self):
        self.api_key = settings.mailgun_api_key
        self.domain = settings.mailgun_domain
        self.api_url = settings.mailgun_api_url
        self.from_email = settings.email_from
        self.from_name = settings.email_from_name
        self.dry_run = settings.email_dry_run

        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render_template(self, template_name: str, **context) -> tuple[str, str | None]:
        """Render an email template.

        Returns (html_content, text_content) tuple.
        Text content is None if no .txt template exists.
        """
        html_template = self.jinja_env.get_template(f"{template_name}.html")
        html_content = html_template.render(**context)

        text_content = None
        try:
            text_template = self.jinja_env.get_template(f"{template_name}.txt")
            text_content = text_template.render(**context)
        except Exception:
            # Text template is optional
            pass

        return html_content, text_content

    async def send(self, message: EmailMessage) -> bool:
        """Send an email via Mailgun.

        In dry_run mode, logs the email instead of sending.
        Returns True if successful (or dry run), False otherwise.
        Always sends HTML form; text is optional fallback.
        """
        if self.dry_run:
            logger.info(
                "DRY RUN - Would send email:\n"
                f"  To: {message.to}\n"
                f"  BCC: {message.bcc}\n"
                f"  Subject: {message.subject}\n"
                f"  Reply-To: {message.reply_to}"
                f"\n\n{message.html}"
            )
            return True

        if not self.api_key or not self.domain:
            logger.error("Mailgun API key or domain not configured")
            return False

        # Build the request data - always send HTML
        data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": message.to,
            "subject": message.subject,
            "html": message.html,
        }

        # Optional text fallback
        if message.text:
            data["text"] = message.text

        if message.bcc:
            data["bcc"] = message.bcc

        if message.reply_to:
            data["h:Reply-To"] = message.reply_to

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/{self.domain}/messages",
                    auth=("api", self.api_key),
                    data=data,
                )
                response.raise_for_status()
                logger.info(f"Email sent successfully to {message.to}")
                return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Mailgun API error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    async def send_signup_confirmation(
        self,
        to_email: str,
        caregiver_name: str,
        child_name: str,
        session_name: str,
        session_venue: str | None,
        session_address: str,
        session_time: str,
        term_summary: str | None,
        what_to_bring: str | None,
        signup_status: str,
        signup_id: str,
        session_id: str,
        bcc_emails: list[str] | None = None,
    ) -> bool:
        """Send a signup confirmation email (direct to caregiver, no BCC)."""
        calendar_url = f"{settings.public_base_url}/api/v1/session/{session_id}/calendar.ics"

        if not term_summary:
            term_summary = "Term dates to be confirmed"
        if not what_to_bring:
            what_to_bring = (
                "Bring a water bottle. If your child has a laptop or device they can bring it, but it's not required."
            )

        html, text = self.render_template(
            "signup_confirmation",
            caregiver_name=caregiver_name,
            child_name=child_name,
            session_name=session_name,
            session_venue=session_venue or session_name,
            session_address=session_address,
            session_time=session_time,
            term_summary=term_summary,
            what_to_bring=what_to_bring,
            signup_status=signup_status,
            signup_id=signup_id,
            calendar_url=calendar_url,
            is_waitlisted=signup_status == "waitlisted",
            contact_email=settings.email_contact,
        )

        status_text = "Confirmed" if signup_status == "confirmed" else "Waitlisted"
        subject = f"Signup {status_text}: {child_name} for {session_name}"

        message = EmailMessage(
            to=[to_email],
            subject=subject,
            html=html,
            text=text,
            reply_to=settings.email_contact,
        )

        return await self.send(message)

    async def send_magic_link_login(
        self,
        *,
        to_email: str,
        magic_link_url: str,
        caregiver_name: str | None = None,
        ttl_minutes: int = 15,
    ) -> bool:
        html, text = self.render_template(
            "magic_link_login",
            caregiver_name=caregiver_name,
            magic_link_url=magic_link_url,
            ttl_minutes=ttl_minutes,
        )

        message = EmailMessage(
            to=[to_email],
            subject="Your sign-in link for Tūhura Tech Sessions",
            html=html,
            text=text,
            reply_to=settings.email_contact,
        )

        return await self.send(message)


# Singleton instance
email_service = EmailService()

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ParsedSessionTime:
    weekday: int  # Monday=0
    start: time
    end: time


_WEEKDAYS: dict[str, int] = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


_TIME_RE = re.compile(
    r"^(?P<weekday>[A-Za-z]+)\s+at\s+"
    r"(?P<start>\d{1,2}(?::\d{2})?)(?P<start_ampm>am|pm)?\s*-\s*"
    r"(?P<end>\d{1,2}(?::\d{2})?)(?P<end_ampm>am|pm)?\s*$",
    re.IGNORECASE,
)


def _parse_clock(raw: str, ampm: str | None) -> time:
    h, m = (raw.split(":") + ["0"])[:2]
    hour = int(h)
    minute = int(m)
    if ampm:
        ampm = ampm.lower()
        if hour == 12:
            hour = 0
        if ampm == "pm":
            hour += 12
    return time(hour=hour, minute=minute)


def parse_session_time(value: str) -> ParsedSessionTime | None:
    """Parse session time strings like 'Tuesday at 3:30 - 5:30pm'.

    Returns None if parsing fails.
    """
    if not value:
        return None
    match = _TIME_RE.match(value.strip())
    if not match:
        return None

    weekday_raw = match.group("weekday").lower()
    weekday = _WEEKDAYS.get(weekday_raw)
    if weekday is None:
        return None

    start_raw = match.group("start")
    start_ampm = match.group("start_ampm")
    end_raw = match.group("end")
    end_ampm = match.group("end_ampm")

    # If only one side specifies am/pm, apply it to the other side.
    if not start_ampm and end_ampm:
        start_ampm = end_ampm
    elif start_ampm and not end_ampm:
        end_ampm = start_ampm

    try:
        start_t = _parse_clock(start_raw, start_ampm)
        end_t = _parse_clock(end_raw, end_ampm)
    except Exception:
        return None

    return ParsedSessionTime(weekday=weekday, start=start_t, end=end_t)


def next_occurrence(
    parsed: ParsedSessionTime,
    *,
    tz: ZoneInfo,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Compute the next local occurrence of the parsed weekday/time."""
    now_local = now.astimezone(tz) if now else datetime.now(tz)

    days_ahead = (parsed.weekday - now_local.weekday() + 7) % 7
    today_date = now_local.date()
    candidate_date = today_date + timedelta(days=days_ahead)

    start_dt = datetime.combine(candidate_date, parsed.start, tzinfo=tz)
    end_dt = datetime.combine(candidate_date, parsed.end, tzinfo=tz)

    # If it's today but already started (or ended), move to next week.
    if days_ahead == 0 and start_dt <= now_local:
        candidate_date = today_date + timedelta(days=7)
        start_dt = datetime.combine(candidate_date, parsed.start, tzinfo=tz)
        end_dt = datetime.combine(candidate_date, parsed.end, tzinfo=tz)

    # Handle end time that crosses midnight (rare but safe).
    if end_dt <= start_dt:
        end_dt = end_dt + timedelta(days=1)

    return start_dt, end_dt


def _ics_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def build_session_calendar_feed(
    *,
    session_id: str,
    session_name: str,
    occurrences: list[tuple[datetime, datetime, bool, str | None]],
    location: str,
    address: str,
    tzid: str,
    url: str | None = None,
    refresh_interval_hours: int = 24,
) -> str:
    """Create a subscribable calendar feed with multiple occurrences.

    Args:
            session_id: Unique session identifier
            session_name: Display name of the session
            occurrences: List of (start, end, cancelled, cancellation_reason) tuples
            location: Venue name
            address: Venue address
            tzid: Timezone identifier (e.g., 'Pacific/Auckland')
            url: Optional session details URL
            refresh_interval_hours: How often calendar clients should refresh (default 24h)
    """
    dtstamp = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Tuhura Tech//Sessions//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_ics_escape(session_name)}",
        f"X-WR-CALDESC:Tūhura Tech Session: {_ics_escape(session_name)}",
        f"X-WR-TIMEZONE:{_ics_escape(tzid)}",
        # Tell calendar clients to refresh every N hours
        f"REFRESH-INTERVAL;VALUE=DURATION:PT{refresh_interval_hours}H",
        f"X-PUBLISHED-TTL:PT{refresh_interval_hours}H",
    ]

    # Add each occurrence as a separate VEVENT
    for idx, (start, end, cancelled, cancel_reason) in enumerate(occurrences):
        start_local = start.strftime("%Y%m%dT%H%M%S")
        end_local = end.strftime("%Y%m%dT%H%M%S")

        # Unique UID for each occurrence
        uid = f"session-{session_id}-occ-{idx}@tuhuratech.org.nz"

        summary = f"Tūhura Tech: {session_name}"
        if cancelled:
            summary = f"CANCELLED - {summary}"

        description_parts = [session_name]
        if address:
            description_parts.append(address)
        if cancelled and cancel_reason:
            description_parts.append(f"Cancelled: {cancel_reason}")
        description = "\\n".join(description_parts)

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_ics_escape(uid)}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;TZID={_ics_escape(tzid)}:{start_local}",
                f"DTEND;TZID={_ics_escape(tzid)}:{end_local}",
                f"SUMMARY:{_ics_escape(summary)}",
                f"LOCATION:{_ics_escape(location)}",
                f"DESCRIPTION:{_ics_escape(description)}",
                f"SEQUENCE:{idx}",  # Version number for updates
            ]
        )

        if cancelled:
            lines.append("STATUS:CANCELLED")

        if url:
            lines.append(f"URL:{_ics_escape(url)}")

        lines.append("END:VEVENT")

    lines.extend(["END:VCALENDAR", ""])
    return "\r\n".join(lines)

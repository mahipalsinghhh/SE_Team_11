"""Email wording. Times are shown in the lab's own time zone."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app import models as m


def local(dt_utc: datetime, tz: str) -> datetime:
    return dt_utc.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz))


def slot_text(r: m.Reservation) -> str:
    tz = r.equipment.lab.timezone
    s, e = local(r.start_utc, tz), local(r.end_utc, tz)
    return f"{r.equipment.name} ({r.equipment.lab.name}) on {s:%a %d %b %Y}, {s:%H:%M}-{e:%H:%M} ({tz})"


def reminder_email(r: m.Reservation) -> tuple[str, str]:
    subject = f"Reminder: your lab booking #{r.id} starts soon"
    body = (f"Hello {r.user.name},\n\n"
            f"This is a reminder of your booking: {slot_text(r)}.\n\n"
            f"If you can no longer attend, please cancel it so others can use the slot.\n\n"
            f"Remote Lab Reservation System")
    return subject, body


def maintenance_cancel_email(r: m.Reservation, reason: str) -> tuple[str, str]:
    subject = f"Your lab booking #{r.id} was cancelled for maintenance"
    body = (f"Hello {r.user.name},\n\n"
            f"Your booking {slot_text(r)} has been cancelled because the equipment is "
            f"blocked for maintenance" + (f": {reason}" if reason else "") + ".\n\n"
            f"Please choose another slot in the calendar.\n\n"
            f"Remote Lab Reservation System")
    return subject, body

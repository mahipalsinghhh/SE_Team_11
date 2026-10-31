"""RLRS-13 (part): attendance marking (RLRS-F-018)."""
from __future__ import annotations
from datetime import datetime
from .types import Reservation, Status


class AttendanceError(Exception):
    pass


def mark_attendance(res: Reservation, outcome: Status, now: datetime) -> Reservation:
    if outcome not in (Status.COMPLETED, Status.NO_SHOW):
        raise AttendanceError("Outcome must be Completed or NoShow.")
    if res.status != Status.CONFIRMED:
        raise AttendanceError(f"Only Confirmed reservations can be marked (is {res.status.value}).")
    if now < res.interval.end:
        raise AttendanceError("Cannot mark attendance before the slot has ended.")
    res.status = outcome
    return res

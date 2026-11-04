"""RLRS-13: mark a finished reservation Completed or No-show (RLRS-F-018)."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from rlrs_core.attendance import AttendanceError, mark_attendance
from rlrs_core.types import Status

from app import models as m
from app.engine import convert
from app.engine.audit import record_audit


class NotFound(Exception):
    pass


def mark(session: Session, reservation_id: int, outcome: Status, actor: m.User, now: datetime) -> m.Reservation:
    """Raises NotFound, or rlrs_core AttendanceError (slot not ended / wrong status).
    Caller commits."""
    res = session.get(m.Reservation, reservation_id)
    if res is None:
        raise NotFound(f"Reservation {reservation_id} not found.")
    before = res.status
    core = mark_attendance(convert.reservation(res), outcome, now)  # rules live in rlrs_core
    res.status = core.status.value
    record_audit(session, actor, "attendance.marked", "reservation", res.id, now,
                 from_status=before, to_status=res.status)
    return res


__all__ = ["mark", "NotFound", "AttendanceError"]

"""RLRS-5: booking rules validation (RLRS-F-009). Values come from LabConfig."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Iterable
from .types import ACTIVE, Interval, Reservation


@dataclass(frozen=True)
class LabConfig:
    open_time: time = time(9, 0)
    close_time: time = time(18, 0)
    slot_minutes: int = 30
    max_duration_minutes: int = 120
    advance_days: int = 14
    max_active_per_user: int = 3


@dataclass(frozen=True)
class Violation:
    code: str
    message: str


def validate_booking(user_id: int, equipment_id: int, interval: Interval, now: datetime,
                     cfg: LabConfig, existing: Iterable[Reservation]) -> list[Violation]:
    """Return all violated rules (empty list means the request is valid)."""
    v: list[Violation] = []
    s, e = interval.start, interval.end

    if s < now:
        v.append(Violation("PAST_START", "Start time is in the past."))
    if s.date() != e.date() or s.time() < cfg.open_time or e.time() > cfg.close_time:
        v.append(Violation("OUTSIDE_HOURS",
                           f"Booking must be within {cfg.open_time:%H:%M}-{cfg.close_time:%H:%M} on one day."))
    else:
        opened = datetime.combine(s.date(), cfg.open_time)
        off_grid = ((s - opened).total_seconds() / 60) % cfg.slot_minutes != 0 or \
                   interval.minutes % cfg.slot_minutes != 0
        if off_grid:
            v.append(Violation("OFF_GRID", f"Times must align to {cfg.slot_minutes}-minute slots."))
    if s > now + timedelta(days=cfg.advance_days):
        v.append(Violation("TOO_FAR_AHEAD", f"Cannot book more than {cfg.advance_days} days ahead."))
    if interval.minutes > cfg.max_duration_minutes:
        v.append(Violation("TOO_LONG", f"Maximum duration is {cfg.max_duration_minutes} minutes."))

    mine = [r for r in existing if r.user_id == user_id and r.status in ACTIVE]
    if len(mine) >= cfg.max_active_per_user:
        v.append(Violation("TOO_MANY_ACTIVE", f"Maximum {cfg.max_active_per_user} active bookings per user."))
    if any(r.interval.overlaps(interval) for r in mine):
        v.append(Violation("USER_OVERLAP", "You already have a booking overlapping this time."))
    return v

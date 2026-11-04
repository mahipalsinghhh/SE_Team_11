"""RLRS-14: utilisation and no-show report (RLRS-F-019).

Counting rules come from rlrs_core.report.utilisation_report. This module supplies the
"available hours" per equipment: the lab's opening hours (in the lab's own time zone) that
fall inside the chosen window, minus time the equipment was blocked for maintenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from rlrs_core.report import utilisation_report
from rlrs_core.types import Interval

from app import models as m
from app.engine import convert

Span = tuple[datetime, datetime]


def _clip(a: Span, b: Span) -> Span | None:
    s, e = max(a[0], b[0]), min(a[1], b[1])
    return (s, e) if s < e else None


def _merge(spans: list[Span]) -> list[Span]:
    out: list[Span] = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def opening_spans(lab: m.Lab, window: Span) -> list[Span]:
    """Opening hours of each local day that touches the window, as naive-UTC spans clipped to it."""
    tz = ZoneInfo(lab.timezone)
    to_local = lambda dt: dt.replace(tzinfo=timezone.utc).astimezone(tz)  # noqa: E731
    to_utc = lambda dt: dt.astimezone(timezone.utc).replace(tzinfo=None)  # noqa: E731
    day, last = to_local(window[0]).date(), to_local(window[1]).date()
    spans = []
    while day <= last:
        o = to_utc(datetime.combine(day, lab.open_time, tz))
        c = to_utc(datetime.combine(day, lab.close_time, tz))
        if (clipped := _clip((o, c), window)):
            spans.append(clipped)
        day += timedelta(days=1)
    return spans


def available_hours(open_spans: list[Span], blocks: list[Span]) -> float:
    total = sum((e - s).total_seconds() for s, e in open_spans)
    blocked = 0.0
    for b in _merge(blocks):
        for o in open_spans:
            if (x := _clip(o, b)):
                blocked += (x[1] - x[0]).total_seconds()
    return max(total - blocked, 0.0) / 3600


@dataclass
class ReportRow:
    lab_id: int
    lab: str
    equipment_id: int
    equipment: str
    booked_hours: float
    available_hours: float
    utilisation_pct: float
    bookings: int
    cancellations: int
    no_shows: int


def build_report(session: Session, start: datetime, end: datetime, lab_id: int | None = None) -> list[ReportRow]:
    window = (start, end)
    eq_q = select(m.Equipment).order_by(m.Equipment.lab_id, m.Equipment.id)
    if lab_id is not None:
        eq_q = eq_q.where(m.Equipment.lab_id == lab_id)
    equipment = list(session.scalars(eq_q))
    ids = [e.id for e in equipment]
    if not ids:
        return []

    blocks: dict[int, list[Span]] = {i: [] for i in ids}
    for b in session.scalars(select(m.MaintenanceBlock).where(
            m.MaintenanceBlock.equipment_id.in_(ids),
            m.MaintenanceBlock.start_utc < end, m.MaintenanceBlock.end_utc > start)):
        blocks[b.equipment_id].append((b.start_utc, b.end_utc))

    open_cache: dict[int, list[Span]] = {}
    avail = {}
    for e in equipment:
        if e.lab_id not in open_cache:
            open_cache[e.lab_id] = opening_spans(e.lab, window)
        avail[e.id] = available_hours(open_cache[e.lab_id], blocks[e.id])

    reservations = [convert.reservation(r) for r in session.scalars(select(m.Reservation).where(
        m.Reservation.equipment_id.in_(ids), m.Reservation.start_utc < end, m.Reservation.end_utc > start))]
    core = utilisation_report(reservations, avail, Interval(start, end))

    return [ReportRow(e.lab_id, e.lab.name, e.id, e.name,
                      round(core[e.id].booked_hours, 2), round(core[e.id].available_hours, 2),
                      core[e.id].utilisation_pct, core[e.id].bookings, core[e.id].cancellations,
                      core[e.id].no_shows)
            for e in equipment]

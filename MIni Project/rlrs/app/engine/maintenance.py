"""RLRS-12: maintenance blocks (RLRS-F-013).

create_block() does everything in ONE transaction (the caller's session, BEGIN IMMEDIATE):
  1. insert the block,
  2. cancel every active reservation inside it (rule from rlrs_core.maintenance.apply_block),
  3. cancel those reservations' pending reminders,
  4. queue a cancellation email per holder in the outbox,
  5. write audit rows.
If anything fails, none of it is committed. The worker delivers the queued emails after commit.

slot_conflicts() is the guard the booking endpoint (RLRS-6) must call before inserting, so new
bookings inside a maintenance block are rejected. It uses rlrs_core.conflict.find_conflicts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from rlrs_core.conflict import Conflict, find_conflicts
from rlrs_core.maintenance import apply_block
from rlrs_core.types import Interval

from app import models as m
from app.engine import convert, notify
from app.engine.audit import record_audit
from app.engine.outbox import queue_email
from app.engine.reminders import ACTIVE_VALUES, cancel_reminders


class NotFound(Exception):
    pass


class InvalidBlock(Exception):
    pass


@dataclass
class BlockResult:
    block: m.MaintenanceBlock
    cancelled: list[m.Reservation]


def _overlapping(session: Session, equipment_id: int, start: datetime, end: datetime):
    """Rows overlapping [start, end): cheap SQL pre-filter; exact rule is applied by rlrs_core."""
    res = list(session.scalars(select(m.Reservation).where(
        m.Reservation.equipment_id == equipment_id,
        m.Reservation.status.in_(ACTIVE_VALUES),
        m.Reservation.start_utc < end, m.Reservation.end_utc > start)))
    blocks = list(session.scalars(select(m.MaintenanceBlock).where(
        m.MaintenanceBlock.equipment_id == equipment_id,
        m.MaintenanceBlock.start_utc < end, m.MaintenanceBlock.end_utc > start)))
    return res, blocks


def slot_conflicts(session: Session, equipment_id: int, start: datetime, end: datetime) -> list[Conflict]:
    """Every reservation or maintenance block that would clash with a booking [start, end)."""
    res, blocks = _overlapping(session, equipment_id, start, end)
    return find_conflicts(equipment_id, Interval(start, end),
                          [convert.reservation(r) for r in res], [convert.block(b) for b in blocks])


def create_block(session: Session, equipment_id: int, start: datetime, end: datetime, reason: str,
                 actor: m.User, now: datetime) -> BlockResult:
    if end <= start:
        raise InvalidBlock("End must be after start.")
    if end <= now:
        raise InvalidBlock("Maintenance block is entirely in the past.")
    if session.get(m.Equipment, equipment_id) is None:
        raise NotFound(f"Equipment {equipment_id} not found.")

    block = m.MaintenanceBlock(equipment_id=equipment_id, start_utc=start, end_utc=end,
                               reason=reason, created_by=actor.id, created_at=now)
    session.add(block)
    session.flush()

    rows, _ = _overlapping(session, equipment_id, start, end)
    by_id = {r.id: r for r in rows}
    hit_ids = {c.id for c in apply_block(convert.block(block), [convert.reservation(r) for r in rows])}
    cancelled = [by_id[i] for i in sorted(hit_ids)]

    for r in cancelled:
        r.status = "Cancelled"
        subject, body = notify.maintenance_cancel_email(r, reason)
        queue_email(session, r.user.email, subject, body, now)
        record_audit(session, actor, "reservation.cancelled_by_maintenance", "reservation", r.id, now,
                     maintenance_block_id=block.id)
    cancel_reminders(session, hit_ids)
    record_audit(session, actor, "maintenance.created", "maintenance_block", block.id, now,
                 equipment_id=equipment_id, start_utc=start, end_utc=end, reason=reason,
                 cancelled_reservation_ids=sorted(hit_ids))
    return BlockResult(block, cancelled)

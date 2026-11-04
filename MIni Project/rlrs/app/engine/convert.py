"""ORM row -> rlrs_core value conversions."""
from __future__ import annotations

from rlrs_core import types as core

from app import models as m


def reservation(r: m.Reservation) -> core.Reservation:
    return core.Reservation(r.id, r.user_id, r.equipment_id,
                            core.Interval(r.start_utc, r.end_utc), core.Status(r.status))


def block(b: m.MaintenanceBlock) -> core.MaintenanceBlock:
    return core.MaintenanceBlock(b.id, b.equipment_id, core.Interval(b.start_utc, b.end_utc), b.reason)

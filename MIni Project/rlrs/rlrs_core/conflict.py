"""RLRS-4: conflict detection (RLRS-F-008)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Union
from .types import ACTIVE, Interval, MaintenanceBlock, Reservation


@dataclass(frozen=True)
class Conflict:
    kind: str  # "reservation" or "maintenance"
    id: int
    interval: Interval


def find_conflicts(equipment_id: int, candidate: Interval,
                   reservations: Iterable[Reservation],
                   blocks: Iterable[MaintenanceBlock] = ()) -> list[Conflict]:
    """Return every active reservation / maintenance block overlapping candidate.

    Cancelled, rejected, completed and no-show reservations never conflict,
    so a cancelled slot can be booked again.
    """
    found: list[Conflict] = []
    for r in reservations:
        if r.equipment_id == equipment_id and r.status in ACTIVE and r.interval.overlaps(candidate):
            found.append(Conflict("reservation", r.id, r.interval))
    for b in blocks:
        if b.equipment_id == equipment_id and b.interval.overlaps(candidate):
            found.append(Conflict("maintenance", b.id, b.interval))
    return found


def is_free(equipment_id: int, candidate: Interval, reservations, blocks=()) -> bool:
    return not find_conflicts(equipment_id, candidate, reservations, blocks)

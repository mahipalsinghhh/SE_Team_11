"""RLRS-12: maintenance blocks (RLRS-F-013)."""
from __future__ import annotations
from typing import Iterable
from .types import ACTIVE, MaintenanceBlock, Reservation, Status


def affected_reservations(block: MaintenanceBlock, reservations: Iterable[Reservation]) -> list[Reservation]:
    return [r for r in reservations
            if r.equipment_id == block.equipment_id and r.status in ACTIVE
            and r.interval.overlaps(block.interval)]


def apply_block(block: MaintenanceBlock, reservations: Iterable[Reservation]) -> list[Reservation]:
    """Cancel every active reservation inside the block and return them so the caller
    can cancel their reminders and notify holders in the same transaction."""
    hit = affected_reservations(block, reservations)
    for r in hit:
        r.status = Status.CANCELLED
    return hit

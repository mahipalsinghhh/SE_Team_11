"""RLRS-14: utilisation and no-show report (RLRS-F-019)."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable
from .types import USED, Interval, Reservation, Status


@dataclass
class EquipmentReport:
    equipment_id: int
    booked_hours: float
    available_hours: float
    bookings: int
    cancellations: int
    no_shows: int

    @property
    def utilisation_pct(self) -> float:
        return round(100 * self.booked_hours / self.available_hours, 2) if self.available_hours else 0.0


def utilisation_report(reservations: Iterable[Reservation], available_hours: Dict[int, float],
                       window: Interval) -> Dict[int, EquipmentReport]:
    """Booked time is clipped to the window. available_hours maps equipment id -> hours
    the equipment could be booked within the window."""
    out = {eid: EquipmentReport(eid, 0.0, hrs, 0, 0, 0) for eid, hrs in available_hours.items()}
    for r in reservations:
        rep = out.get(r.equipment_id)
        if rep is None or not r.interval.overlaps(window):
            continue
        if r.status == Status.CANCELLED:
            rep.cancellations += 1
        if r.status in USED:
            start, end = max(r.interval.start, window.start), min(r.interval.end, window.end)
            rep.booked_hours += (end - start).total_seconds() / 3600
            rep.bookings += 1
        if r.status == Status.NO_SHOW:
            rep.no_shows += 1
    return out

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class Status(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    COMPLETED = "Completed"
    NO_SHOW = "NoShow"


# Statuses that occupy the equipment's time slot.
ACTIVE = {Status.PENDING, Status.CONFIRMED}
# Statuses that count as "booked time" in utilisation reports.
USED = {Status.CONFIRMED, Status.COMPLETED, Status.NO_SHOW}


@dataclass(frozen=True)
class Interval:
    """Half-open time range [start, end). Touching ranges do not overlap."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("end must be after start")

    def overlaps(self, other: "Interval") -> bool:
        return self.start < other.end and other.start < self.end

    @property
    def minutes(self) -> float:
        return (self.end - self.start).total_seconds() / 60


@dataclass
class Reservation:
    id: int
    user_id: int
    equipment_id: int
    interval: Interval
    status: Status = Status.CONFIRMED


@dataclass(frozen=True)
class MaintenanceBlock:
    id: int
    equipment_id: int
    interval: Interval
    reason: str = ""

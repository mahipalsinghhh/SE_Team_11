from datetime import datetime, timedelta
from rlrs_core.types import Interval, Reservation, Status

NOW = datetime(2026, 11, 2, 8, 0)


def iv(day_offset, sh, sm, eh, em):
    d = (NOW + timedelta(days=day_offset)).date()
    return Interval(datetime(d.year, d.month, d.day, sh, sm), datetime(d.year, d.month, d.day, eh, em))


def res(i, uid, eq, interval, status=Status.CONFIRMED):
    return Reservation(i, uid, eq, interval, status)

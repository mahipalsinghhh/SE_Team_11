"""RLRS-5 | TC-RULE-01..04 (defaults: 09:00-18:00, 30-min slots, max 120 min, 14 days, 3 active)"""
from datetime import timedelta
from rlrs_core.rules import LabConfig, validate_booking
from rlrs_core.types import Interval, Status
from .helpers import NOW, iv, res

CFG = LabConfig()


def codes(interval, existing=(), now=NOW, uid=1):
    return {v.code for v in validate_booking(uid, 7, interval, now, CFG, existing)}


def test_valid_booking_has_no_violations():
    assert codes(iv(1, 10, 0, 11, 0)) == set()


def test_past_start():
    assert "PAST_START" in codes(iv(-1, 10, 0, 11, 0))


def test_outside_hours_boundaries():
    assert "OUTSIDE_HOURS" in codes(iv(1, 8, 30, 9, 30))
    assert "OUTSIDE_HOURS" in codes(iv(1, 17, 30, 18, 30))
    assert codes(iv(1, 9, 0, 10, 0)) == set()      # exactly at opening
    assert codes(iv(1, 17, 0, 18, 0)) == set()     # exactly at closing


def test_multi_day_booking_rejected():
    i = Interval(iv(1, 17, 0, 17, 30).start, iv(2, 9, 30, 10, 0).end)
    assert "OUTSIDE_HOURS" in codes(i)


def test_off_grid():
    assert "OFF_GRID" in codes(iv(1, 10, 10, 11, 0))
    assert "OFF_GRID" in codes(iv(1, 10, 0, 10, 45))


def test_advance_window_edge():
    assert "TOO_FAR_AHEAD" in codes(iv(14, 10, 0, 11, 0))   # 14d+2h after now(08:00)
    assert "TOO_FAR_AHEAD" in codes(iv(15, 10, 0, 11, 0))
    assert "TOO_FAR_AHEAD" not in codes(iv(13, 10, 0, 11, 0))


def test_max_duration_edge():
    assert "TOO_LONG" not in codes(iv(1, 10, 0, 12, 0))   # exactly 120
    assert "TOO_LONG" in codes(iv(1, 10, 0, 12, 30))      # 150


def test_max_active_per_user():
    mine = [res(i, 1, 100 + i, iv(2, 9 + i, 0, 10 + i, 0)) for i in range(3)]
    assert "TOO_MANY_ACTIVE" in codes(iv(1, 10, 0, 11, 0), mine)
    mine[0].status = Status.CANCELLED  # cancelled do not count
    assert "TOO_MANY_ACTIVE" not in codes(iv(1, 10, 0, 11, 0), mine)


def test_user_cannot_double_book_same_time_on_other_equipment():
    mine = [res(1, 1, 99, iv(1, 10, 0, 11, 0))]
    assert "USER_OVERLAP" in codes(iv(1, 10, 30, 11, 30), mine)
    assert "USER_OVERLAP" not in codes(iv(1, 10, 30, 11, 30), mine, uid=2)


def test_all_violations_reported_together():
    c = codes(iv(-1, 8, 0, 11, 10))
    assert {"PAST_START", "OUTSIDE_HOURS", "TOO_LONG"} <= c

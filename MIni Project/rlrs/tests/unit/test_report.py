"""RLRS-14 | TC-REP-01 (known dataset, hand-calculated expected values)"""
from rlrs_core.report import utilisation_report
from rlrs_core.types import Status
from .helpers import iv, res

WINDOW = iv(1, 9, 0, 17, 0)   # 8 available hours for each equipment


def test_known_dataset_reconciles():
    data = [
        res(1, 1, 7, iv(1, 9, 0, 11, 0), Status.COMPLETED),   # 2h used
        res(2, 2, 7, iv(1, 11, 0, 12, 0), Status.NO_SHOW),    # 1h used, no-show
        res(3, 3, 7, iv(1, 13, 0, 14, 0), Status.CANCELLED),  # not used, cancellation
        res(4, 4, 7, iv(1, 15, 0, 16, 0), Status.CONFIRMED),  # 1h used
        res(5, 5, 8, iv(1, 9, 0, 10, 0), Status.CONFIRMED),   # 1h used on other equipment
    ]
    rep = utilisation_report(data, {7: 8.0, 8: 8.0}, WINDOW)
    a = rep[7]
    assert (a.booked_hours, a.bookings, a.cancellations, a.no_shows) == (4.0, 3, 1, 1)
    assert a.utilisation_pct == 50.0
    assert rep[8].booked_hours == 1.0 and rep[8].utilisation_pct == 12.5


def test_booking_outside_window_ignored_and_partial_clipped():
    data = [res(1, 1, 7, iv(2, 9, 0, 10, 0), Status.CONFIRMED),          # next day: ignored
            res(2, 2, 7, iv(1, 8, 0, 10, 0), Status.CONFIRMED)]          # 08-10 clipped to 09-10
    rep = utilisation_report(data, {7: 8.0}, WINDOW)
    assert rep[7].booked_hours == 1.0 and rep[7].bookings == 1


def test_zero_available_hours_gives_zero_pct():
    assert utilisation_report([], {7: 0.0}, WINDOW)[7].utilisation_pct == 0.0

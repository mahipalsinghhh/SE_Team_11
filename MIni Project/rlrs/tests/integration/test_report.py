"""RLRS-14 integration tests. Test Plan: TC-REP-01 (figures reconcile on a known dataset).

Known dataset, lab open 09:00-18:00 IST, window Mon 2 Nov 00:00 IST -> Wed 4 Nov 00:00 IST
(two lab days = 18 open hours per equipment):

Oscilloscope 1 (eq1)
  maintenance 2 Nov 10:00-12:00                 -> available 18 - 2 = 16 h
  2 Nov 13:00-15:00 Completed                   -> 2 h booked
  2 Nov 15:00-16:00 NoShow                      -> 1 h booked, 1 no-show
  3 Nov 09:00-10:00 Confirmed                   -> 1 h booked
  3 Nov 11:00-12:00 Cancelled                   -> 1 cancellation, not booked time
  4 Nov 09:00-10:00 Confirmed (outside window)  -> ignored
  => booked 4 h / 16 h = 25 %, bookings 3, cancellations 1, no-shows 1
3D Printer (eq2): nothing booked => 0 / 18 h, 0 %
"""
from datetime import datetime, timedelta

from app.models import MaintenanceBlock

from .conftest import NOW, as_user, make_reservation

IST = timedelta(hours=5, minutes=30)


def ist(day, h, mi=0):
    """Naive UTC for a wall-clock time in IST in November 2026."""
    return datetime(2026, 11, day, h, mi) - IST


def q(start, end, **extra):
    return {"from": start, "to": end, **extra}


WINDOW = q("2026-11-02T00:00:00+05:30", "2026-11-04T00:00:00+05:30")


def load_dataset(session, seed):
    s, e1 = seed["student"], seed["eq1"]
    session.add(MaintenanceBlock(equipment_id=e1.id, start_utc=ist(2, 10), end_utc=ist(2, 12),
                                 reason="Calibration", created_at=NOW))
    session.commit()
    make_reservation(session, s, e1, ist(2, 13), ist(2, 15), "Completed")
    make_reservation(session, s, e1, ist(2, 15), ist(2, 16), "NoShow")
    make_reservation(session, s, e1, ist(3, 9), ist(3, 10), "Confirmed")
    make_reservation(session, s, e1, ist(3, 11), ist(3, 12), "Cancelled")
    make_reservation(session, s, e1, ist(4, 9), ist(4, 10), "Confirmed")


def test_rep_01_known_dataset_reconciles(client, session, seed):
    load_dataset(session, seed)
    r = client.get("/api/reports/utilisation", params=WINDOW, headers=as_user(seed["incharge"]))
    assert r.status_code == 200
    body = r.json()
    assert body["from_utc"] == "2026-11-01T18:30:00"
    rows = {row["equipment"]: row for row in body["rows"]}
    assert rows["Oscilloscope 1"] == {
        "lab_id": seed["lab"].id, "lab": "Robotics Lab", "equipment_id": seed["eq1"].id,
        "equipment": "Oscilloscope 1", "booked_hours": 4.0, "available_hours": 16.0,
        "utilisation_pct": 25.0, "bookings": 3, "cancellations": 1, "no_shows": 1}
    assert rows["3D Printer"]["booked_hours"] == 0.0
    assert rows["3D Printer"]["available_hours"] == 18.0
    assert rows["3D Printer"]["utilisation_pct"] == 0.0


def test_partial_window_clips_booked_and_open_hours(client, session, seed):
    load_dataset(session, seed)
    # 2 Nov 14:00 -> 17:00 IST: open 3 h, Completed contributes 1 h, NoShow 1 h
    r = client.get("/api/reports/utilisation", headers=as_user(seed["incharge"]),
                   params=q("2026-11-02T14:00:00+05:30", "2026-11-02T17:00:00+05:30")).json()
    row = next(x for x in r["rows"] if x["equipment"] == "Oscilloscope 1")
    assert (row["booked_hours"], row["available_hours"], row["bookings"]) == (2.0, 3.0, 2)


def test_overlapping_maintenance_blocks_not_double_counted(client, session, seed):
    for s, e in [(10, 12), (11, 13)]:
        session.add(MaintenanceBlock(equipment_id=seed["eq1"].id, start_utc=ist(2, s), end_utc=ist(2, e),
                                     created_at=NOW))
    session.commit()
    r = client.get("/api/reports/utilisation", params=WINDOW, headers=as_user(seed["admin"])).json()
    row = next(x for x in r["rows"] if x["equipment"] == "Oscilloscope 1")
    assert row["available_hours"] == 15.0  # 18 - 3 (10:00-13:00 merged)


def test_lab_filter_and_validation(client, session, seed):
    h = as_user(seed["incharge"])
    assert client.get("/api/reports/utilisation", params={**WINDOW, "lab_id": 999}, headers=h).json()["rows"] == []
    assert len(client.get("/api/reports/utilisation", params={**WINDOW, "lab_id": seed["lab"].id},
                          headers=h).json()["rows"]) == 2
    bad = q("2026-11-04T00:00:00+05:30", "2026-11-02T00:00:00+05:30")
    assert client.get("/api/reports/utilisation", params=bad, headers=h).status_code == 422
    assert client.get("/api/reports/utilisation", params=WINDOW, headers=as_user(seed["student"])).status_code == 403

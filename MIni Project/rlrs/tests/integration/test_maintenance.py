"""RLRS-12 integration tests. Test Plan: TC-MAINT-01."""
from datetime import timedelta
from unittest.mock import patch

import pytest

from app.engine import maintenance
from app.engine.reminders import schedule_reminder
from app.models import AuditEvent, MaintenanceBlock, OutboxEmail, ReminderJob, Reservation
from app.worker.runner import run_cycle

from .conftest import NOW, as_user, make_reservation

H = timedelta(hours=1)
T0 = NOW + 24 * H  # tomorrow, same time


def booked(session, seed, start, end, user="student", eq="eq1", status="Confirmed"):
    r = make_reservation(session, seed[user], seed[eq], start, end, status)
    schedule_reminder(session, r, NOW)
    session.commit()
    return r


def post_block(client, seed, start, end, eq="eq1", who="incharge", reason="Calibration"):
    return client.post("/api/maintenance-blocks", headers=as_user(seed[who]), json={
        "equipment_id": seed[eq].id, "start": start.isoformat() + "Z", "end": end.isoformat() + "Z",
        "reason": reason})


def test_tc_maint_01_block_cancels_overlapping_and_notifies(client, app, session, seed, mailer):
    inside = booked(session, seed, T0 + H, T0 + 2 * H)
    partly = booked(session, seed, T0 + 3 * H + timedelta(minutes=30), T0 + 4 * H + timedelta(minutes=30), user="student2")
    before = booked(session, seed, T0, T0 + H)               # ends exactly when block starts
    other_eq = booked(session, seed, T0 + H, T0 + 2 * H, eq="eq2", user="student2")
    already_cancelled = booked(session, seed, T0 + 2 * H, T0 + 3 * H, status="Cancelled")

    resp = post_block(client, seed, T0 + H, T0 + 4 * H)
    assert resp.status_code == 201
    body = resp.json()
    assert sorted(body["cancelled_reservation_ids"]) == sorted([inside.id, partly.id])

    session.expire_all()
    status = {r.id: r.status for r in session.query(Reservation)}
    assert status[inside.id] == status[partly.id] == "Cancelled"
    assert status[before.id] == status[other_eq.id] == "Confirmed"
    assert status[already_cancelled.id] == "Cancelled"

    jobs = {j.reservation_id: j.status for j in session.query(ReminderJob)}
    assert jobs[inside.id] == jobs[partly.id] == "Cancelled"
    assert jobs[before.id] == jobs[other_eq.id] == "Pending"

    queued = session.query(OutboxEmail).all()
    assert sorted(e.to for e in queued) == ["student2@example.test", "student@example.test"]
    assert all("cancelled for maintenance" in e.subject for e in queued)
    assert "Calibration" in queued[0].body

    # emails go out on the next worker run
    run_cycle(app.state.session_factory, mailer, app.state.settings, NOW)
    assert len([m for m in mailer.sent if "maintenance" in m[1]]) == 2

    actions = sorted(a.action for a in session.query(AuditEvent))
    assert actions == ["maintenance.created", "reservation.cancelled_by_maintenance",
                       "reservation.cancelled_by_maintenance"]


def test_tc_maint_01_new_booking_inside_block_is_rejected(client, session, seed):
    post_block(client, seed, T0 + H, T0 + 3 * H)
    clash = maintenance.slot_conflicts(session, seed["eq1"].id, T0 + 2 * H, T0 + 2 * H + timedelta(minutes=30))
    assert [c.kind for c in clash] == ["maintenance"]
    assert maintenance.slot_conflicts(session, seed["eq1"].id, T0 + 3 * H, T0 + 4 * H) == []  # back-to-back ok
    assert maintenance.slot_conflicts(session, seed["eq2"].id, T0 + 2 * H, T0 + 3 * H) == []  # other equipment


def test_tc_maint_01_shows_as_maintenance_on_the_calendar_feed(client, session, seed):
    r = booked(session, seed, T0 + 5 * H, T0 + 6 * H)
    post_block(client, seed, T0 + H, T0 + 2 * H)
    feed = client.get(f"/api/equipment/{seed['eq1'].id}/schedule",
                      params={"from": (T0).isoformat() + "Z", "to": (T0 + 8 * H).isoformat() + "Z"}).json()
    assert [(i["kind"], i["reason"] if i["kind"] == "maintenance" else i["id"]) for i in feed] == \
           [("maintenance", "Calibration"), ("reservation", r.id)]
    assert "user_id" not in feed[1]


def test_all_or_nothing_when_something_fails(client, session, seed):
    r = booked(session, seed, T0 + H, T0 + 2 * H)
    with patch("app.engine.maintenance.queue_email", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            post_block(client, seed, T0, T0 + 3 * H)
    session.expire_all()
    assert session.query(MaintenanceBlock).count() == 0
    assert session.get(Reservation, r.id).status == "Confirmed"
    assert session.query(ReminderJob).one().status == "Pending"
    assert session.query(AuditEvent).count() == 0


def test_validation_and_permissions(client, seed):
    assert post_block(client, seed, T0 + H, T0).status_code == 422                # end before start
    assert post_block(client, seed, NOW - 3 * H, NOW - H).status_code == 422      # in the past
    assert client.post("/api/maintenance-blocks", headers=as_user(seed["incharge"]), json={
        "equipment_id": 999, "start": (T0).isoformat(), "end": (T0 + H).isoformat()}).status_code == 404
    assert post_block(client, seed, T0, T0 + H, who="student").status_code == 403


def test_timezone_offset_input_is_stored_as_utc(client, session, seed):
    # 10:00-11:00 IST tomorrow == 04:30-05:30 UTC
    d = (T0).date()
    resp = client.post("/api/maintenance-blocks", headers=as_user(seed["incharge"]), json={
        "equipment_id": seed["eq1"].id,
        "start": f"{d}T10:00:00+05:30", "end": f"{d}T11:00:00+05:30"})
    assert resp.status_code == 201
    assert resp.json()["block"]["start_utc"] == f"{d}T04:30:00"

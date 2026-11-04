"""RLRS-13 integration tests. Test Plan: TC-ATT-01, TC-AUDIT-01."""
from datetime import timedelta

from app.engine.audit import record_audit
from app.models import AuditEvent, Reservation

from .conftest import NOW, as_user, make_reservation

H = timedelta(hours=1)


def finished(session, seed, status="Confirmed"):
    return make_reservation(session, seed["student"], seed["eq1"], NOW - 2 * H, NOW - H, status)


def test_tc_att_01_mark_completed_and_no_show(client, session, seed):
    r1 = finished(session, seed)
    r2 = make_reservation(session, seed["student2"], seed["eq2"], NOW - 2 * H, NOW - H)
    a = client.post(f"/api/reservations/{r1.id}/attendance", json={"outcome": "Completed"},
                    headers=as_user(seed["incharge"]))
    b = client.post(f"/api/reservations/{r2.id}/attendance", json={"outcome": "NoShow"},
                    headers=as_user(seed["admin"]))
    assert (a.status_code, a.json()["status"]) == (200, "Completed")
    assert (b.status_code, b.json()["status"]) == (200, "NoShow")
    session.expire_all()
    assert session.get(Reservation, r1.id).status == "Completed"


def test_tc_att_01_marking_before_slot_ends_is_409(client, session, seed):
    r = make_reservation(session, seed["student"], seed["eq1"], NOW - H, NOW + H)  # in progress
    resp = client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "Completed"},
                       headers=as_user(seed["incharge"]))
    assert resp.status_code == 409
    assert "before the slot has ended" in resp.json()["detail"]
    session.expire_all()
    assert session.get(Reservation, r.id).status == "Confirmed"
    assert session.query(AuditEvent).count() == 0  # failed change -> no audit row


def test_cannot_mark_cancelled_or_already_marked(client, session, seed):
    r = finished(session, seed, status="Cancelled")
    assert client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "NoShow"},
                       headers=as_user(seed["incharge"])).status_code == 409
    r2 = finished(session, seed)
    h = as_user(seed["incharge"])
    assert client.post(f"/api/reservations/{r2.id}/attendance", json={"outcome": "NoShow"}, headers=h).status_code == 200
    assert client.post(f"/api/reservations/{r2.id}/attendance", json={"outcome": "Completed"}, headers=h).status_code == 409


def test_bad_outcome_404_and_permissions(client, session, seed):
    r = finished(session, seed)
    h = as_user(seed["incharge"])
    assert client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "Cancelled"}, headers=h).status_code == 422
    assert client.post("/api/reservations/9999/attendance", json={"outcome": "NoShow"}, headers=h).status_code == 404
    assert client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "NoShow"},
                       headers=as_user(seed["student"])).status_code == 403
    assert client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "NoShow"}).status_code == 401


def test_tc_audit_01_records_actor_action_and_time(client, session, seed, clock):
    r = finished(session, seed)
    client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "NoShow"},
                headers=as_user(seed["incharge"]))
    log = client.get("/api/audit", headers=as_user(seed["admin"])).json()
    assert len(log) == 1
    ev = log[0]
    assert ev["actor"] == "incharge@example.test (lab_incharge)"
    assert ev["action"] == "attendance.marked"
    assert (ev["entity"], ev["entity_id"]) == ("reservation", r.id)
    assert ev["at"].startswith(clock.now.isoformat())
    assert ev["details"] == {"from_status": "Confirmed", "to_status": "NoShow"}


def test_tc_audit_01_never_stores_secrets(session, seed):
    record_audit(session, seed["admin"], "user.password_changed", "user", seed["student"].id, NOW,
                 password="hunter2", new_password="x", api_key="k", note="ok")
    session.commit()
    raw = session.query(AuditEvent).one().details
    assert raw == {"password": "[REDACTED]", "new_password": "[REDACTED]",
                   "api_key": "[REDACTED]", "note": "ok"}
    assert "hunter2" not in str(raw)


def test_students_cannot_read_audit_log(client, seed):
    assert client.get("/api/audit", headers=as_user(seed["student"])).status_code == 403


def test_tc_att_01_no_show_is_counted_in_the_report(client, session, seed):
    """TC-ATT-01 expected result: 'Status No-show; counted in no-show report.'"""
    r = finished(session, seed)
    h = as_user(seed["incharge"])
    assert client.post(f"/api/reservations/{r.id}/attendance", json={"outcome": "NoShow"}, headers=h).status_code == 200
    rep = client.get("/api/reports/utilisation", headers=h, params={
        "from": (NOW - 24 * H).isoformat() + "Z", "to": (NOW + H).isoformat() + "Z"}).json()
    row = next(x for x in rep["rows"] if x["equipment_id"] == seed["eq1"].id)
    assert (row["no_shows"], row["bookings"], row["booked_hours"]) == (1, 1, 1.0)

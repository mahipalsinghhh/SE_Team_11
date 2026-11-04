"""RLRS-10 integration tests: real SQLite, fake clock (no waiting), fake mailer.

Test Plan cases: TC-MAIL-01 (sent before slot), TC-MAIL-02 (no reminder for cancelled/rejected),
TC-MAIL-03 (retry then Failed), TC-RESTART-01 (exactly once across reruns/restart).
"""
from datetime import timedelta

from app.config import Settings
from app.engine.reminders import cancel_reminders, run_reminders, schedule_reminder
from app.main import create_app
from app.models import ReminderJob
from app.worker.runner import run_cycle

from .conftest import NOW, FakeMailer, as_user, make_reservation

H = timedelta(hours=1)


def book(session, seed, start, end, status="Confirmed", user="student"):
    r = make_reservation(session, seed[user], seed["eq1"], start, end, status)
    job = schedule_reminder(session, r, NOW)
    session.commit()
    return r, job


def run(app, mailer, now, **kw):
    return run_reminders(app.state.session_factory, now, mailer.send, **kw)


def test_mail_01_reminder_sent_two_hours_before(app, session, seed, mailer):
    r, job = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    assert job.send_at == NOW + 3 * H

    assert run(app, mailer, NOW + 3 * H - timedelta(minutes=1))["sent"] == 0
    assert mailer.sent == []

    assert run(app, mailer, NOW + 3 * H)["sent"] == 1
    to, subject, body = mailer.sent[0]
    assert to == "student@example.test"
    assert f"#{r.id}" in subject
    # 09:00 UTC = 14:30 IST: shown in the lab's time zone
    assert "14:30-15:30 (Asia/Kolkata)" in body
    session.expire_all()
    assert session.get(ReminderJob, job.id).status == "Sent"


def test_booking_inside_lead_window_reminds_at_next_run(app, session, seed, mailer):
    _, job = book(session, seed, NOW + timedelta(minutes=60), NOW + 2 * H)
    assert job.send_at == NOW
    assert run(app, mailer, NOW)["sent"] == 1


def test_no_job_for_slot_already_started(session, seed):
    r = make_reservation(session, seed["student"], seed["eq1"], NOW - H, NOW + H)
    assert schedule_reminder(session, r, NOW) is None


def test_schedule_is_idempotent(session, seed):
    r, job = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    again = schedule_reminder(session, r, NOW)
    session.commit()
    assert again.id == job.id
    assert session.query(ReminderJob).count() == 1


def test_mail_02_no_reminder_for_cancelled_or_rejected(app, session, seed, mailer):
    r1, j1 = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    r2, j2 = book(session, seed, NOW + 7 * H, NOW + 8 * H, user="student2")
    # status changes after the job was planned, without cancelling the job first
    r1.status = "Cancelled"
    r2.status = "Rejected"
    session.commit()

    stats = run(app, mailer, NOW + 6 * H)
    assert stats["cancelled"] == 2 and stats["sent"] == 0
    assert mailer.sent == []


def test_cancel_reminders_marks_pending_jobs(app, session, seed, mailer):
    r, job = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    assert cancel_reminders(session, [r.id]) == 1
    session.commit()
    assert run(app, mailer, NOW + 4 * H)["sent"] == 0
    session.expire_all()
    assert session.get(ReminderJob, job.id).status == "Cancelled"


def test_mail_03_temporary_failure_retried_then_sent(app, session, seed):
    _, job = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    flaky = FakeMailer(fail_times=1)
    t = NOW + 3 * H
    assert run(app, flaky, t)["retry"] == 1
    session.expire_all()
    j = session.get(ReminderJob, job.id)
    assert j.status == "Pending" and j.attempts == 1 and "ConnectionError" in j.last_error

    assert run(app, flaky, t + timedelta(minutes=1))["sent"] == 0  # back-off not over
    assert run(app, flaky, t + timedelta(minutes=5))["sent"] == 1
    assert len(flaky.sent) == 1


def test_mail_03_repeated_failure_marks_failed(app, session, seed):
    _, job = book(session, seed, NOW + 5 * H, NOW + 6 * H)
    down = FakeMailer(fail_times=99)
    t = NOW + 3 * H
    results = [run(app, down, t + timedelta(minutes=5 * i)) for i in range(4)]
    assert [x["retry"] for x in results[:2]] == [1, 1]
    assert results[2]["failed"] == 1
    assert results[3] == {"sent": 0, "retry": 0, "failed": 0, "cancelled": 0}
    session.expire_all()
    j = session.get(ReminderJob, job.id)
    assert j.status == "Failed" and j.attempts == 3


def test_restart_01_exactly_once_across_reruns_and_restart(tmp_path, mailer):
    """Run the worker twice, then build a brand-new app on the same database file
    (a restart) and run again: the reminder goes out exactly once."""
    from datetime import time
    from app.models import Equipment, Lab, Role, User

    url = f"sqlite:///{tmp_path / 'restart.db'}"
    s1 = Settings(database_url=url, worker_enabled=False)
    app1 = create_app(s1, mailer=mailer, start_worker=False)
    with app1.state.session_factory() as s:
        lab = Lab(name="L", open_time=time(9), close_time=time(18))
        s.add(lab); s.flush()
        eq = Equipment(lab_id=lab.id, name="E")
        u = User(name="U", email="u@example.test", role=Role.STUDENT.value)
        s.add_all([eq, u]); s.commit()
        r = make_reservation(s, u, eq, NOW + 5 * H, NOW + 6 * H)
        schedule_reminder(s, r, NOW); s.commit()

    due = NOW + 3 * H
    run_cycle(app1.state.session_factory, mailer, s1, due)
    run_cycle(app1.state.session_factory, mailer, s1, due)
    app1.state.engine.dispose()

    app2 = create_app(s1, mailer=mailer, start_worker=False)  # "restart"
    run_cycle(app2.state.session_factory, mailer, s1, due + H)
    assert len(mailer.sent) == 1


def test_two_workers_at_the_same_time_send_each_reminder_once(app, session, seed):
    import threading
    import time as _time

    for i in range(10):
        book(session, seed, NOW + (5 + i) * H, NOW + (5 + i) * H + timedelta(minutes=30),
             user="student" if i % 2 else "student2")

    class SlowMailer(FakeMailer):
        def send(self, to, subject, body):
            _time.sleep(0.01)  # widen the race window
            super().send(to, subject, body)

    shared = SlowMailer()
    start = threading.Barrier(2)

    def worker():
        start.wait()
        run(app, shared, NOW + 4 * H)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    subjects = [s for _, s, _ in shared.sent]
    assert len(subjects) == len(set(subjects))  # no duplicates
    assert len(subjects) == 2  # slots starting at +5h and +6h are due at +4h (send_at = start-2h)


def test_staff_can_list_reminders_students_cannot(client, session, seed):
    book(session, seed, NOW + 5 * H, NOW + 6 * H)
    ok = client.get("/api/reminders", headers=as_user(seed["incharge"]))
    assert ok.status_code == 200 and ok.json()[0]["status"] == "Pending"
    assert client.get("/api/reminders", headers=as_user(seed["student"])).status_code == 403
    assert client.get("/api/reminders").status_code == 401

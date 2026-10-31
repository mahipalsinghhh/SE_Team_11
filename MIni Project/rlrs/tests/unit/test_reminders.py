"""RLRS-10 | TC-MAIL-01..03, TC-RESTART-01 (fake clock, fake sender)"""
from datetime import timedelta
from rlrs_core.reminders import JobStatus, cancel_jobs_for, plan_reminder, process_due
from rlrs_core.types import Status
from .helpers import NOW, iv, res

R = res(1, 1, 7, iv(1, 10, 0, 11, 0))
START = R.interval.start


def test_reminder_scheduled_two_hours_before():
    job = plan_reminder(R, NOW)
    assert job.send_at == START - timedelta(hours=2)


def test_no_reminder_if_already_started():
    assert plan_reminder(R, START) is None


def test_booking_inside_lead_window_sends_immediately():
    soon = res(2, 1, 7, iv(0, 9, 0, 9, 30))
    job = plan_reminder(soon, NOW)
    assert job.send_at == NOW


def test_not_sent_before_due_time():
    sent = []
    job = plan_reminder(R, NOW)
    process_due([job], {1: R}, START - timedelta(hours=3), sent.append)
    assert sent == [] and job.status == JobStatus.PENDING


def test_sent_exactly_once_even_if_worker_runs_twice():
    sent = []
    job = plan_reminder(R, NOW)
    t = START - timedelta(hours=2)
    process_due([job], {1: R}, t, sent.append)
    process_due([job], {1: R}, t + timedelta(minutes=1), sent.append)   # restart / second worker
    assert len(sent) == 1 and job.status == JobStatus.SENT


def test_no_reminder_for_cancelled_or_rejected():
    for st in (Status.CANCELLED, Status.REJECTED):
        r = res(3, 1, 7, iv(1, 10, 0, 11, 0), st)
        sent = []
        job = plan_reminder(r, NOW)
        process_due([job], {3: r}, START, sent.append)
        assert sent == [] and job.status == JobStatus.CANCELLED


def test_cancel_jobs_for_reservation():
    job = plan_reminder(R, NOW)
    assert cancel_jobs_for([job], {1}) == 1 and job.status == JobStatus.CANCELLED


def test_temporary_failure_is_retried_then_succeeds():
    calls = {"n": 0}

    def flaky(_):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("smtp down")

    job = plan_reminder(R, NOW)
    t = START - timedelta(hours=2)
    s1 = process_due([job], {1: R}, t, flaky)
    assert s1["retry"] == 1 and job.status == JobStatus.PENDING and job.attempts == 1
    process_due([job], {1: R}, t + timedelta(minutes=1), flaky)          # backoff not elapsed
    assert calls["n"] == 1
    s2 = process_due([job], {1: R}, t + timedelta(minutes=6), flaky)
    assert s2["sent"] == 1 and job.status == JobStatus.SENT and calls["n"] == 2


def test_repeated_failure_marks_failed():
    def down(_):
        raise ConnectionError("smtp down")

    job = plan_reminder(R, NOW)
    t = START - timedelta(hours=2)
    for k in range(5):
        process_due([job], {1: R}, t + timedelta(minutes=10 * k), down)
    assert job.status == JobStatus.FAILED and job.attempts == 3

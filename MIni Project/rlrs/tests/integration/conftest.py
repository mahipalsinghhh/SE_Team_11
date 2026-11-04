"""Integration fixtures: a real SQLite file per test, a fixed clock and a fake mailer."""
from __future__ import annotations

from datetime import datetime, time, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_now
from app.config import Settings
from app.main import create_app
from app.models import Equipment, Lab, Reservation, Role, User

NOW = datetime(2026, 11, 9, 4, 0)  # 09:30 IST on demo day, stored as naive UTC


class FakeMailer:
    def __init__(self, fail_times: int = 0):
        self.sent: list[tuple[str, str, str]] = []
        self.fail_times = fail_times

    def send(self, to: str, subject: str, body: str) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("SMTP temporarily unavailable")
        self.sent.append((to, subject, body))


class Clock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, **kw) -> None:
        self.now += timedelta(**kw)


@pytest.fixture
def clock():
    return Clock(NOW)


@pytest.fixture
def mailer():
    return FakeMailer()


@pytest.fixture
def app(tmp_path, clock, mailer):
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}", worker_enabled=False)
    application = create_app(settings, mailer=mailer, start_worker=False)
    application.dependency_overrides[get_now] = clock
    return application


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def session(app):
    s = app.state.session_factory()
    yield s
    s.close()


@pytest.fixture
def seed(session):
    """One lab (09:00-18:00 IST), two pieces of equipment, a student, a lab in-charge, an admin."""
    lab = Lab(name="Robotics Lab", timezone="Asia/Kolkata", open_time=time(9), close_time=time(18))
    session.add(lab)
    session.flush()
    eq1 = Equipment(lab_id=lab.id, name="Oscilloscope 1")
    eq2 = Equipment(lab_id=lab.id, name="3D Printer")
    student = User(name="Test Student", email="student@example.test", role=Role.STUDENT.value)
    student2 = User(name="Second Student", email="student2@example.test", role=Role.STUDENT.value)
    incharge = User(name="Lab In-charge", email="incharge@example.test", role=Role.LAB_INCHARGE.value)
    admin = User(name="Admin", email="admin@example.test", role=Role.ADMIN.value)
    session.add_all([eq1, eq2, student, student2, incharge, admin])
    session.commit()
    return {"lab": lab, "eq1": eq1, "eq2": eq2, "student": student, "student2": student2,
            "incharge": incharge, "admin": admin}


def make_reservation(session, user, equipment, start, end, status="Confirmed") -> Reservation:
    r = Reservation(user_id=user.id, equipment_id=equipment.id, start_utc=start, end_utc=end,
                    status=status, created_at=NOW)
    session.add(r)
    session.commit()
    return r


def as_user(user) -> dict:
    return {"X-User-Id": str(user.id)}

"""Load demo data into the database named by RLRS_DATABASE_URL (default ./rlrs.db).

    python scripts/seed_demo.py            # refuses if data already exists
    python scripts/seed_demo.py --reset    # wipes all tables first

Creates one lab, three pieces of equipment, users (ids printed: use them in the X-User-Id
header until RLRS-2 sign-in exists) and a few bookings around "now", including one starting in
90 minutes so the reminder worker sends an email on its next run. All emails are @example.test.
"""
from __future__ import annotations

import sys
from datetime import time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.db import make_engine, make_session_factory, utcnow  # noqa: E402
from app.engine.reminders import schedule_reminder  # noqa: E402
from app.models import Base, Equipment, Lab, Reservation, Role, User  # noqa: E402


def main(reset: bool) -> None:
    settings = Settings.from_env()
    engine = make_engine(settings.database_url)
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sf = make_session_factory(engine)
    now = utcnow().replace(second=0, microsecond=0)
    now -= timedelta(minutes=now.minute % 30)  # align to the 30-minute grid
    lead = timedelta(minutes=settings.reminder_lead_minutes)

    with sf() as s:
        if s.query(User).count():
            sys.exit("Database already has data. Use --reset to wipe it.")
        lab = Lab(name="Embedded Systems Lab", timezone="Asia/Kolkata", open_time=time(0), close_time=time(23, 59))
        s.add(lab)
        s.flush()
        eqs = [Equipment(lab_id=lab.id, name=n) for n in ("Oscilloscope 1", "Logic Analyser", "3D Printer")]
        users = [
            User(name="Asha Student", email="asha@example.test", role=Role.STUDENT.value),
            User(name="Ravi Student", email="ravi@example.test", role=Role.STUDENT.value),
            User(name="Lab In-charge", email="incharge@example.test", role=Role.LAB_INCHARGE.value),
            User(name="Admin", email="admin@example.test", role=Role.ADMIN.value),
        ]
        s.add_all(eqs + users)
        s.flush()
        asha, ravi = users[0], users[1]
        bookings = [
            (asha, eqs[0], now - timedelta(hours=3), now - timedelta(hours=2)),  # finished: mark attendance
            (ravi, eqs[0], now - timedelta(hours=2), now - timedelta(hours=1)),  # finished
            (asha, eqs[0], now + timedelta(minutes=90), now + timedelta(minutes=150)),  # reminder due now
            (ravi, eqs[1], now + timedelta(days=1), now + timedelta(days=1, hours=1)),  # maintenance demo
        ]
        for u, e, st, en in bookings:
            r = Reservation(user_id=u.id, equipment_id=e.id, start_utc=st, end_utc=en,
                            status="Confirmed", created_at=now)
            s.add(r)
            s.flush()
            schedule_reminder(s, r, now, lead)
        s.commit()
        print("Users (X-User-Id):")
        for u in users:
            print(f"  {u.id}  {u.role:<13} {u.email}")
        print("Equipment:", ", ".join(f"{e.id}={e.name}" for e in eqs))
        print(f"Created {len(bookings)} reservations; times stored in UTC around {now:%Y-%m-%d %H:%M} UTC.")


if __name__ == "__main__":
    main("--reset" in sys.argv)

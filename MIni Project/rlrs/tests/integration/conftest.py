from datetime import datetime
import pytest
from rlrs_app import db, seed, service
from rlrs_app.mailer import FileTransport

NOW = datetime(2026, 11, 6, 8, 0)  # Friday 08:00, lab opens 09:00


@pytest.fixture
def conn(tmp_path):
    c = db.connect(str(tmp_path / "t.db"))
    db.init_db(c)
    seed.seed(c)
    yield c
    c.close()


def user(conn, email):
    return dict(conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone())


@pytest.fixture
def s1(conn): return user(conn, "student1@lab.test")
@pytest.fixture
def s2(conn): return user(conn, "student2@lab.test")
@pytest.fixture
def staff(conn): return user(conn, "incharge@lab.test")
@pytest.fixture
def admin(conn): return user(conn, "admin@lab.test")
@pytest.fixture
def transport(tmp_path): return FileTransport(str(tmp_path / "outbox"))

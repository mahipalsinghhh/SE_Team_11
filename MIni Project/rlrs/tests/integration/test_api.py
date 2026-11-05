"""API tests over real HTTP against the stdlib server (fake clock, temp DB, file mail transport)."""
import json
import threading
import urllib.error
import urllib.request
from datetime import datetime
import pytest
from rlrs_app import db, seed, server
from rlrs_app.mailer import FileTransport
from .conftest import NOW

D = "2026-11-09"


class Client:
    def __init__(self, base):
        self.base, self.cookie = base, None

    def call(self, method, path, body=None):
        req = urllib.request.Request(self.base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **({"Cookie": self.cookie} if self.cookie else {})})
        try:
            with urllib.request.urlopen(req) as r:
                sc = r.headers.get("Set-Cookie")
                if sc:
                    self.cookie = sc.split(";")[0]
                return r.status, json.loads(r.read() or b"null"), r
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                return e.code, json.loads(raw), e
            except ValueError:
                return e.code, raw.decode(), e

    def login(self, email, pw):
        s, b, _ = self.call("POST", "/api/login", {"email": email, "password": pw})
        assert s == 200, b
        return self


@pytest.fixture
def base(tmp_path):
    path = str(tmp_path / "api.db")
    srv = server.make_server(path, "127.0.0.1", 0, lambda: NOW, FileTransport(str(tmp_path / "out")))
    c = db.connect(path)
    seed.seed(c)
    c.close()
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_requires_login_and_session_lifecycle(base):
    c = Client(base)
    assert c.call("GET", "/api/equipment")[0] == 401
    assert c.call("GET", "/api/me")[0] == 401
    assert c.call("POST", "/api/login", {"email": "student1@lab.test", "password": "nope"})[0] == 401
    c.login("student1@lab.test", "student123")
    s, me, r = c.call("GET", "/api/me")
    assert s == 200 and me["role"] == "Student" and "pw_hash" not in me
    c.call("POST", "/api/logout")
    assert c.call("GET", "/api/me")[0] == 401


def test_cookie_is_httponly(base):
    _, _, r = Client(base).call("POST", "/api/login", {"email": "student1@lab.test", "password": "student123"})
    assert "HttpOnly" in r.headers["Set-Cookie"]


def test_role_enforcement_is_server_side(base):
    st = Client(base).login("student1@lab.test", "student123")
    assert st.call("POST", "/api/equipment", {"lab_id": 1, "name": "Hack"})[0] == 403
    assert st.call("GET", "/api/audit")[0] == 403
    assert st.call("GET", "/api/reports/utilisation?from=2026-11-09&to=2026-11-09")[0] == 403
    assert st.call("POST", "/api/maintenance", {"equipment_id": 1, "start": f"{D}T09:00", "end": f"{D}T10:00"})[0] == 403
    ic = Client(base).login("incharge@lab.test", "incharge123")
    assert ic.call("GET", "/api/audit")[0] == 200


def test_booking_over_http_201_400_409(base):
    a = Client(base).login("student1@lab.test", "student123")
    b = Client(base).login("student2@lab.test", "student123")
    s, r, _ = a.call("POST", "/api/reservations", {"equipment_id": 1, "start": f"{D}T10:00", "end": f"{D}T11:00"})
    assert s == 201 and r["status"] == "Confirmed"
    s, r, _ = b.call("POST", "/api/reservations", {"equipment_id": 1, "start": f"{D}T10:30", "end": f"{D}T11:30"})
    assert s == 409 and r["error"] == "CONFLICT" and r["details"][0]["start"].startswith(f"{D}T10:00")
    s, r, _ = b.call("POST", "/api/reservations", {"equipment_id": 1, "start": f"{D}T08:00", "end": f"{D}T09:00"})
    assert s == 400 and r["error"] == "RULE_VIOLATION" and r["details"][0]["code"] == "OUTSIDE_HOURS"
    s, mine, _ = a.call("GET", "/api/reservations/mine")
    assert s == 200 and len(mine) == 1
    s, av, _ = b.call("GET", f"/api/equipment/1/availability?from={D}&to={D}")
    assert {x["start"][11:16]: x["state"] for x in av["slots"]}["10:00"] == "booked"


def test_cancel_over_http_and_other_user_forbidden(base):
    a = Client(base).login("student1@lab.test", "student123")
    b = Client(base).login("student2@lab.test", "student123")
    rid = a.call("POST", "/api/reservations", {"equipment_id": 1, "start": f"{D}T10:00", "end": f"{D}T11:00"})[1]["id"]
    assert b.call("POST", f"/api/reservations/{rid}/cancel")[0] == 403
    assert a.call("POST", f"/api/reservations/{rid}/cancel")[1]["status"] == "Cancelled"
    assert a.call("POST", f"/api/reservations/{rid}/cancel")[0] == 409


def test_approval_flow_over_http(base):
    a = Client(base).login("student1@lab.test", "student123")
    ic = Client(base).login("incharge@lab.test", "incharge123")
    rid = a.call("POST", "/api/reservations", {"equipment_id": 3, "start": f"{D}T10:00", "end": f"{D}T11:00"})[1]["id"]
    s, pend, _ = ic.call("GET", "/api/reservations/manage?status=Pending")
    assert s == 200 and [p["id"] for p in pend] == [rid]
    assert a.call("POST", f"/api/reservations/{rid}/approve")[0] == 403
    assert ic.call("POST", f"/api/reservations/{rid}/reject", {"reason": ""})[0] == 400
    assert ic.call("POST", f"/api/reservations/{rid}/approve")[1]["status"] == "Confirmed"


def test_errors_are_json_without_stack_traces(base):
    c = Client(base).login("student1@lab.test", "student123")
    for path, body in [("/api/reservations", {"equipment_id": "abc"}), ("/api/reservations", {"equipment_id": 1, "start": "x", "end": "y"}),
                       ("/api/equipment/99999/availability?from=2026-11-09&to=2026-11-09", None)]:
        s, r, _ = c.call("POST" if body is not None else "GET", path, body)
        assert s in (400, 404) and "Traceback" not in json.dumps(r) and r["error"]
    req = urllib.request.Request(base + "/api/reservations", method="POST", data=b"{not json", headers={"Cookie": c.cookie})
    with pytest.raises(urllib.error.HTTPError) as ex:
        urllib.request.urlopen(req)
    assert ex.value.code == 400 and b"BAD_JSON" in ex.value.read()
    assert c.call("GET", "/api/nope")[0] == 404


def test_sql_injection_strings_are_inert(base):
    c = Client(base)
    s, _, _ = c.call("POST", "/api/login", {"email": "' OR '1'='1", "password": "' OR '1'='1"})
    assert s == 401
    c.login("student1@lab.test", "student123")
    s, r, _ = c.call("GET", "/api/equipment?q=%27%3B%20DROP%20TABLE%20users%3B--")
    assert s == 200 and r == []
    assert Client(base).login("student2@lab.test", "student123").call("GET", "/api/me")[0] == 200  # users table intact


def test_static_page_served_and_path_traversal_blocked(base):
    with urllib.request.urlopen(base + "/") as r:
        assert r.status == 200 and b"RLRS" in r.read()
    for p in ("/../service.py", "/..%2fservice.py", "/%2e%2e/service.py", "/static/../../db.py"):
        try:
            urllib.request.urlopen(base + p)
            raise AssertionError(f"served {p}")
        except urllib.error.HTTPError as e:
            assert e.code == 404


def test_health_endpoint_is_public_and_checks_db(base):
    """RLRS-1: /api/health answers without login and confirms the database is reachable."""
    s, b, _ = Client(base).call("GET", "/api/health")
    assert s == 200
    assert b["status"] == "ok" and b["db"] == "ok"
    assert Client(base).call("POST", "/api/health")[0] in (404, 405)

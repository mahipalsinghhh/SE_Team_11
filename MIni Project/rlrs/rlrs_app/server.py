"""RLRS HTTP server: standard library only (http.server + sqlite3).

Run:  python -m rlrs_app.server --seed        then open http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
import time
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import db, mailer, seed as seed_mod, service
from .service import ApiError

STATIC = Path(__file__).parent / "static"
MAX_BODY = 1_000_000
COOKIE = "rlrs_session"
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8"}


def _q1(query, key, default=None):
    v = query.get(key)
    return v[0] if v else default


def _int(v, what="id"):
    try:
        return int(v)
    except (TypeError, ValueError):
        raise ApiError(400, "BAD_INPUT", f"Invalid {what}.")


# route table: (method, regex, needs_login, handler(conn, user, m, query, body, now))
ROUTES = [
    ("GET", r"/api/labs", True, lambda c, u, m, q, b, n: service.list_labs(c)),
    ("PUT", r"/api/labs/(\d+)", True, lambda c, u, m, q, b, n: service.update_lab(c, u, int(m[0]), b, n)),
    ("GET", r"/api/equipment", True, lambda c, u, m, q, b, n: service.list_equipment(c, u, _q1(q, "lab_id"), _q1(q, "type"), _q1(q, "q"))),
    ("POST", r"/api/equipment", True, lambda c, u, m, q, b, n: service.create_equipment(c, u, b, n)),
    ("PUT", r"/api/equipment/(\d+)", True, lambda c, u, m, q, b, n: service.update_equipment(c, u, int(m[0]), b, n)),
    ("GET", r"/api/equipment/(\d+)/availability", True,
     lambda c, u, m, q, b, n: service.availability(c, u, int(m[0]), _q1(q, "from"), _q1(q, "to"), n)),
    ("POST", r"/api/reservations", True,
     lambda c, u, m, q, b, n: service.create_reservation(c, u, _int(b.get("equipment_id"), "equipment_id"), b.get("start"), b.get("end"), n)),
    ("GET", r"/api/reservations/mine", True, lambda c, u, m, q, b, n: service.list_mine(c, u)),
    ("GET", r"/api/reservations/manage", True, lambda c, u, m, q, b, n: service.manage_list(c, u, _q1(q, "status"))),
    ("POST", r"/api/reservations/(\d+)/cancel", True, lambda c, u, m, q, b, n: service.cancel_reservation(c, u, int(m[0]), n)),
    ("POST", r"/api/reservations/(\d+)/approve", True, lambda c, u, m, q, b, n: service.approve_reservation(c, u, int(m[0]), n)),
    ("POST", r"/api/reservations/(\d+)/reject", True, lambda c, u, m, q, b, n: service.reject_reservation(c, u, int(m[0]), b.get("reason"), n)),
    ("POST", r"/api/reservations/(\d+)/attendance", True, lambda c, u, m, q, b, n: service.mark_reservation_attendance(c, u, int(m[0]), b.get("outcome"), n)),
    ("POST", r"/api/maintenance", True,
     lambda c, u, m, q, b, n: service.add_maintenance(c, u, _int(b.get("equipment_id"), "equipment_id"), b.get("start"), b.get("end"), b.get("reason"), n)),
    ("GET", r"/api/reports/utilisation", True, lambda c, u, m, q, b, n: service.utilisation(c, u, _q1(q, "from"), _q1(q, "to"), n)),
    ("GET", r"/api/audit", True, lambda c, u, m, q, b, n: service.audit_list(c, u)),
]


def make_handler(db_path, clock, transport):
    class Handler(BaseHTTPRequestHandler):
        server_version = "RLRS/1.0"

        def log_message(self, fmt, *args):
            if "--quiet" not in sys.argv:
                sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

        # -- plumbing --
        def _send(self, status, payload, extra_headers=()):
            data = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in extra_headers:
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _token(self):
            c = SimpleCookie(self.headers.get("Cookie", ""))
            return c[COOKIE].value if COOKIE in c else None

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                raise ApiError(413, "TOO_LARGE", "Request body too large.")
            if not n:
                return {}
            try:
                body = json.loads(self.rfile.read(n))
            except ValueError:
                raise ApiError(400, "BAD_JSON", "Request body must be valid JSON.")
            if not isinstance(body, dict):
                raise ApiError(400, "BAD_JSON", "Request body must be a JSON object.")
            return body

        def _static(self, path):
            rel = "index.html" if path in ("/", "") else path.lstrip("/")
            f = (STATIC / rel).resolve()
            if STATIC.resolve() not in f.parents or not f.is_file() or f.suffix not in TYPES:
                return self._send(404, {"error": "NOT_FOUND", "message": "Not found."})
            data = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", TYPES[f.suffix])
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        # -- dispatch --
        def _handle(self, method):
            url = urlparse(self.path)
            if not url.path.startswith("/api/"):
                return self._static(url.path) if method == "GET" else self._send(405, {"error": "METHOD", "message": "Method not allowed."})
            conn = db.connect(db_path)
            try:
                now = clock()
                query = parse_qs(url.query)
                if method == "POST" and url.path in ("/api/login", "/api/register", "/api/logout"):
                    return self._auth(conn, url.path, now)
                user = service.user_from_token(conn, self._token(), now)
                if url.path == "/api/me" and method == "GET":
                    if not user:
                        raise ApiError(401, "UNAUTHENTICATED", "Please sign in.")
                    return self._send(200, service.public_user(user))
                for m, pattern, needs_login, fn in ROUTES:
                    mt = re.fullmatch(pattern, url.path)
                    if m == method and mt:
                        if needs_login and not user:
                            raise ApiError(401, "UNAUTHENTICATED", "Please sign in.")
                        body = self._body() if method in ("POST", "PUT") else {}
                        return self._send(201 if (method == "POST" and url.path in ("/api/reservations", "/api/equipment")) else 200,
                                          fn(conn, user, mt.groups(), query, body, now))
                raise ApiError(404, "NOT_FOUND", "Unknown endpoint.")
            except ApiError as e:
                self._send(e.status, {"error": e.code, "message": e.message, "details": e.details})
            except Exception as e:  # never leak stack traces to clients
                sys.stderr.write(f"INTERNAL ERROR {type(e).__name__}: {e}\n")
                self._send(500, {"error": "INTERNAL", "message": "Something went wrong."})
            finally:
                conn.close()

        def _auth(self, conn, path, now):
            if path == "/api/logout":
                service.logout(conn, self._token())
                return self._send(200, {"ok": True}, [("Set-Cookie", f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")])
            b = self._body()
            if path == "/api/register":
                u = service.register_user(conn, b.get("name"), b.get("email"), b.get("password"), "Student", now)
                return self._send(201, u)
            token, user = service.login(conn, b.get("email"), b.get("password"), now)
            self._send(200, user, [("Set-Cookie", f"{COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800")])

        def do_GET(self): self._handle("GET")
        def do_POST(self): self._handle("POST")
        def do_PUT(self): self._handle("PUT")

    return Handler


def make_server(db_path, host="127.0.0.1", port=8000, clock=datetime.now, transport=None):
    conn = db.connect(db_path)
    db.init_db(conn)
    conn.close()
    return ThreadingHTTPServer((host, port), make_handler(db_path, clock, transport or mailer.default_transport()))


def worker_loop(db_path, clock, transport, stop: threading.Event, interval=30):
    while not stop.wait(interval):
        try:
            conn = db.connect(db_path)
            try:
                service.worker_tick(conn, transport, clock())
            finally:
                conn.close()
        except Exception as e:
            sys.stderr.write(f"worker error: {e}\n")


def main():
    ap = argparse.ArgumentParser(description="RLRS server")
    ap.add_argument("--db", default="rlrs.db")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--seed", action="store_true", help="create demo users, labs and equipment if the database is empty")
    ap.add_argument("--worker-interval", type=int, default=30, help="seconds between reminder/email runs")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    transport = mailer.default_transport()
    srv = make_server(a.db, a.host, a.port, datetime.now, transport)
    if a.seed:
        c = db.connect(a.db)
        print("Seeded demo data." if seed_mod.seed(c) else "Database already has data; not seeding.")
        c.close()
    stop = threading.Event()
    threading.Thread(target=worker_loop, args=(a.db, datetime.now, transport, stop, a.worker_interval), daemon=True).start()
    print(f"RLRS running at http://{a.host}:{a.port}  (Ctrl+C to stop). Emails: {type(transport).__name__}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        srv.server_close()


if __name__ == "__main__":
    main()

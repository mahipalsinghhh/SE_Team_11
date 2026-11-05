# RLRS (Remote Lab Reservation System)

Working web app: standard-library Python 3.10+ (http.server + sqlite3) with a plain HTML/JS calendar. **No packages to install.** It is built on the framework-independent logic in `rlrs_core/`.

## Run it (Windows / macOS / Linux)
```
cd "MIni Project/rlrs"
python -m rlrs_app.server --seed          # Windows may need: py -m rlrs_app.server --seed
```
Open http://127.0.0.1:8000. Demo logins (fake data): `student1@lab.test / student123`, `student2@lab.test / student123`, `incharge@lab.test / incharge123`, `admin@lab.test / admin123`.
Emails are written as text files to `./outbox/` (a local mail catcher). To use real SMTP set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` (not yet tested against a real server). A background thread sends reminders and queued emails every 30 s (`--worker-interval`).

## Tests
```
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1      macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v                       # 70 tests
python tests/ui/ui_smoke.py               # browser test; needs: pip install playwright && playwright install chromium
```
Results recorded 5 Nov 2026: `docs/test_evidence_2026-11-05.txt` (67 pytest tests passed, 9/9 browser steps); after the RLRS-6/RLRS-11 gap fixes: `docs/test_evidence_2026-11-05_utc_and_cross_lab.txt` (69 pytest tests passed). Screenshots: `tests/ui/screenshots/`.

Health check (no login): `GET http://127.0.0.1:8000/api/health` returns `{"status": "ok", "db": "ok", ...}`.

CI: `.github/workflows/rlrs-ci.yml` at the **repo root** runs `pytest` on Ubuntu, Windows and macOS for every PR and push to `main`.

## Layout
| Path | What |
|---|---|
| `rlrs_core/` | Pure logic: conflict detection, booking rules, reminders, maintenance, attendance, audit, report |
| `rlrs_app/service.py` | Business operations on SQLite; each booking is one `BEGIN IMMEDIATE` transaction |
| `rlrs_app/server.py` | REST API + static file server + background worker |
| `rlrs_app/static/` | Calendar UI (vanilla JS, no libraries) |
| `tests/unit`, `tests/integration`, `tests/ui` | 37 unit, 33 integration/API tests, browser smoke test |
| `docs/diagrams/` | PlantUML sources (not yet rendered or syntax-checked) |
| `docs/DEMO_SCRIPT.md` | Step-by-step script for the 9 Nov presentation |

## Known deviations from the SRS/SAD (update the documents to match)
- Stack: standard library + SQLite, not FastAPI/SQLAlchemy/APScheduler/FullCalendar (the package index was unreachable while building). The design is still layered: UI, REST API, service layer, pure scheduling logic, data layer, background worker.
- Times are entered and displayed in lab-local time; timestamps are stored in UTC (RLRS-6 met) using the lab's fixed offset from UTC (env var `RLRS_UTC_OFFSET`, default `+05:30` IST). DST-observing zones are not handled (fixed offset, not zoneinfo).
- Not done: HTTPS, CSRF tokens (cookie is HttpOnly + SameSite=Lax), login rate limiting, the 20k-reservation performance test, real SMTP test, running on Windows/macOS (built and tested on Linux only), GitHub Actions run.

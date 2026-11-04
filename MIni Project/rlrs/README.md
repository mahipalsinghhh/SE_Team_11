# RLRS: Remote Lab Reservation System

FastAPI + SQLAlchemy + SQLite + APScheduler, pure-Python domain logic in `rlrs_core/`.
Runs the same on Windows and macOS.

## Folder layout

| Folder | Layer | What lives there |
|---|---|---|
| `app/api/` | REST API | Endpoints. `deps.py` has the DB session, clock, mailer and (temporary) current-user dependencies |
| `app/engine/` | Scheduling engine | Services that load/save ORM rows and call `rlrs_core` for the rules |
| `rlrs_core/` | Scheduling engine | Framework-free logic: conflicts, booking rules, reminders, maintenance, attendance, audit, report |
| `app/models/` | Data layer | SQLAlchemy models. Timestamps are naive UTC; ranges are half-open `[start, end)` |
| `app/worker/` | Reminder worker | Background job (APScheduler) and the SMTP / console mailers |
| `app/ui/` | Browser UI | Static files served at `/ui/` (calendar UI is RLRS-7) |
| `tests/unit/` | | Tests for `rlrs_core` |
| `tests/integration/` | | API + real SQLite tests, fixed clock, fake mailer |

## Run it

**Windows (PowerShell)**
```
cd "MIni Project\rlrs"
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest -v
uvicorn app.main:create_app --factory --reload
```

**macOS / Linux**
```
cd "MIni Project/rlrs"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -v
uvicorn app.main:create_app --factory --reload
```

Then open http://127.0.0.1:8000/health (should return `{"status":"ok","database":"ok"}`) and
http://127.0.0.1:8000/docs for the interactive API docs. The database file `rlrs.db` is created
on first start and is git-ignored.

## Configuration (environment variables, nothing secret in the repo)

| Variable | Default | Meaning |
|---|---|---|
| `RLRS_DATABASE_URL` | `sqlite:///./rlrs.db` | Database location |
| `RLRS_SMTP_HOST` | *(unset)* | Unset = emails are printed to the console instead of sent |
| `RLRS_SMTP_PORT` / `RLRS_SMTP_USER` / `RLRS_SMTP_PASSWORD` / `RLRS_SMTP_FROM` | `587` / – / – / `rlrs@localhost` | SMTP settings |
| `RLRS_SMTP_STARTTLS` | `true` | Use STARTTLS |
| `RLRS_REMINDER_LEAD_MINUTES` | `120` | Reminder sent this long before the slot |
| `RLRS_WORKER_ENABLED` | `true` | Run the background reminder/email worker inside the API process |
| `RLRS_WORKER_INTERVAL_SECONDS` | `60` | How often the worker runs |
| `RLRS_MAX_SEND_ATTEMPTS` / `RLRS_RETRY_BACKOFF_MINUTES` | `3` / `5` | Email retry policy |

For local email testing, run a mail catcher (for example `python -m aiosmtpd -n -l localhost:1025`
after `pip install aiosmtpd`) and set `RLRS_SMTP_HOST=localhost`, `RLRS_SMTP_PORT=1025`,
`RLRS_SMTP_STARTTLS=false`.

## Sign-in (temporary)

Until RLRS-2 adds real sign-in, endpoints identify the caller from the `X-User-Id` header.
Only `app/api/deps.py::current_user` needs to change when RLRS-2 lands.

## CI

`.github/workflows/rlrs-ci.yml` at the **repository root** runs `pytest` on Ubuntu, Windows
and macOS for every push to `main` and every pull request. (The old workflow inside this folder
never ran, because GitHub only reads workflows from the repo root.)

## Status

See the Jira board for what is Done. A story is Done only when its acceptance criteria were
checked, with test output kept in `docs/`.

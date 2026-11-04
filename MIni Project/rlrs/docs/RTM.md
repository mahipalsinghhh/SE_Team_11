# Requirements Traceability Matrix: actual status

**Snapshot:** 5 Nov 2026, branch `feature/RLRS-15-testing-docs`. Replaces the "Not tested" column of SRS v1.0 section 9.
Update this file whenever a story is merged; copy the final version into SRS v1.1 before submission.

Status values:
- **Pass**: built, and the acceptance criterion was checked by a test or live run (evidence linked).
- **Partial**: some of the criterion is built and checked; what is missing is stated.
- **Not built**: no implementation in the repository yet.
- **Not run**: built, but the planned test has not been executed.

Evidence files (in `docs/`): `test_evidence_2026-11-05.txt` (pytest -v, 69 passed), `e2e_evidence_2026-11-05.md`
(live server + worker + real SMTP). Test functions are named after the Test Plan IDs (`test_tc_mail_01_...`).

## Functional requirements

| Req | Requirement (short) | Story / owner | Implementation | Test cases | Status |
|---|---|---|---|---|---|
| RLRS-F-001 | Sign in / sign out | RLRS-2 Deepesh | Placeholder `X-User-Id` header only (`app/api/deps.py`) | TC-AUTH-01 | **Not built** |
| RLRS-F-002 | Role-based permissions | RLRS-2 Deepesh | Role checks enforced in API for staff endpoints (`require_roles`); no real sign-in | TC-AUTH-02 | **Partial**: 403/401 tested on maintenance, attendance, audit, report, reminders endpoints; depends on real sign-in |
| RLRS-F-003 | Manage labs and equipment | RLRS-3 Deepesh | Tables only (`app/models`) | TC-EQ-01, TC-EQ-02 | **Not built** |
| RLRS-F-004 | Operating hours and slot length | RLRS-3 Deepesh | Columns on `labs`; used by report; no endpoint | — | **Not built** |
| RLRS-F-005 | Browse / search equipment | RLRS-3 Deepesh | — | — | **Not built** |
| RLRS-F-006 | Day / week availability calendar | RLRS-7 Deepesh | Feed `GET /api/equipment/{id}/schedule` (busy + maintenance slots); no UI | TC-CAL-01 | **Partial**: feed tested; calendar UI not built |
| RLRS-F-007 | Create reservation | RLRS-6 Lakshya | — | TC-BOOK-01 | **Not built** |
| RLRS-F-008 | Conflict detection | RLRS-4 Lakshya | `rlrs_core/conflict.py`; `slot_conflicts()` wrapper | TC-CONF-01..04 | **Partial**: all four cases pass as unit tests; API 409 needs RLRS-6 |
| RLRS-F-009 | Booking rules | RLRS-5 Lakshya | `rlrs_core/rules.py` | TC-RULE-01..04 | **Partial**: all rules pass as unit tests; API 400 needs RLRS-6 |
| RLRS-F-010 | Approval flow | RLRS-11 Lakshya | — | TC-APPR-01 | **Not built** |
| RLRS-F-011 | My reservations list | RLRS-8 Deepesh | — | — | **Not built** |
| RLRS-F-012 | Cancel own reservation | RLRS-8 Deepesh | `cancel_reminders()` ready for it | TC-CANC-01, TC-CANC-02 | **Not built** |
| RLRS-F-013 | Maintenance blocks cancel + notify | RLRS-12 Mahipal | `app/engine/maintenance.py`, `POST /api/maintenance-blocks` | TC-MAINT-01 | **Partial**: cancel, reminder cancel, email, audit and rollback **Pass**; "new bookings in block rejected" passes at engine level, API needs RLRS-6 to call `slot_conflicts()` |
| RLRS-F-014 | Confirmation / status emails | RLRS-9 Deepesh | Outbox `queue_email()` ready to use; maintenance cancellation email built | TC-BOOK-01 | **Partial**: maintenance cancellation email Pass (live SMTP); confirm/approve/reject emails not built |
| RLRS-F-015 | Reminder email before start | RLRS-10 Mahipal | `app/engine/reminders.py`, worker in `app/worker` | TC-MAIL-02, TC-MAIL-03 | **Pass** (tests + live SMTP). Booking flow must call `schedule_reminder()` (RLRS-6) |
| RLRS-F-016 | Retry failed sends, record status | RLRS-10 Mahipal | Retry/back-off/Failed for reminders and outbox | TC-MAIL-01 | **Pass** for reminders; same code path for outbox emails |
| RLRS-F-017 | Remote-access info to holder only | — | — | TC-SEC-02 | **Not built** |
| RLRS-F-018 | Mark Completed / No-show | RLRS-13 Mahipal | `POST /api/reservations/{id}/attendance` | TC-ATT-01 | **Pass** (incl. 409 before end, and no-show counted in report) |
| RLRS-F-019 | Utilisation report | RLRS-14 Mahipal | `GET /api/reports/utilisation` | TC-REP-01 | **Pass** (hand-calculated dataset reconciles) |
| RLRS-F-020 | Admin configures booking rules | — | Per-lab columns exist; no endpoint | — | **Not built** |
| RLRS-F-021 | Audit events | RLRS-13 Mahipal | `record_audit()`; `GET /api/audit` | TC-AUDIT-01 | **Partial**: attendance + maintenance audited and tested; create/approve/cancel reservation not built (RLRS-6/8/11) |
| RLRS-F-022 | Friendly error messages | all | JSON `detail` messages on 4xx | — | **Not run** |

## Non-functional requirements

| Req | Requirement (short) | Test cases | Status |
|---|---|---|---|
| RLRS-NF-001 | Week view / booking < 2 s on bulk dataset | TC-PERF-01 | **Not run** (calendar and booking not built) |
| RLRS-NF-002 | No double booking under concurrency | TC-CONC-01 | **Not built** for bookings. Locking approach (BEGIN IMMEDIATE) is in place and proven for reminders by a two-worker race test |
| RLRS-NF-003 | Data and reminders survive restart | TC-RESTART-01 | **Pass** for reminders (fresh app on same DB file sends each reminder once) |
| RLRS-NF-004 | Reminder handed to SMTP within 5 min | — | **Partial**: worker runs every 60 s by default; not measured |
| RLRS-NF-005 | No plaintext passwords; auth required | TC-SEC-01 | **Not built** (no passwords exist yet; RLRS-2) |
| RLRS-NF-006 | Usability / accessibility | — | **Not built** (UI) |
| RLRS-NF-007 | Layered, maintainable code | — | **Pass** by inspection: `app/api`, `app/engine` + `rlrs_core`, `app/models`, `app/worker`, `app/ui` |
| RLRS-NF-008 | Documented setup, runs on team machines | — | **Partial**: clean venv on Linux Pass; CI matrix (Windows/macOS/Ubuntu) runs once the PR is opened; manual Windows/macOS run pending |

## Security requirements

| Req | Requirement (short) | Test cases | Status |
|---|---|---|---|
| RLRS-SR-001 | Auth before reservation changes | TC-AUTH-02 | **Partial**: every write endpoint requires an identity (401 tested); real auth is RLRS-2 |
| RLRS-SR-002 | Authorization in API layer | TC-AUTH-02 | **Pass** for built endpoints (403 for students tested on each staff endpoint) |
| RLRS-SR-003 | Salted password hashing | TC-SEC-01 | **Not built** (RLRS-2) |
| RLRS-SR-004 | Server-side validation | — | **Partial**: Pydantic validation; 422 cases tested for maintenance, attendance, report |
| RLRS-SR-005 | Record-level access | TC-SEC-02 | **Not built** |
| RLRS-SR-006 | Secrets via environment, none in repo | TC-SEC-01 | **Pass**: settings only from `RLRS_*` env vars; repo scan on 5 Nov found no hard-coded secrets or real email addresses |
| RLRS-SR-007 | Audit without secrets | TC-AUDIT-01 | **Pass** (redaction tested) |

## Summary (5 Nov)

| | Pass | Partial | Not built | Not run |
|---|---|---|---|---|
| Functional (22) | 4 | 7 | 10 | 1 |
| Non-functional (8) | 2 | 2 | 3 | 1 |
| Security (7) | 3 | 2 | 2 | 0 |

Everything marked Not built belongs to RLRS-2, 3, 6, 7, 8, 9, 11 or has no story yet (F-017, F-020).

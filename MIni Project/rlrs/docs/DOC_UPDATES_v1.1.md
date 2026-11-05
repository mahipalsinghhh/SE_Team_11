# RLRS document updates for v1.1 (SRS, SAD, Test Plan)

**Story:** RLRS-15 (integration testing, evidence, documentation alignment)
**Prepared:** 5 Nov 2026
**Purpose:** The v1.0 PDFs (SRS and SAD dated 30 Oct, Test Plan dated 31 Oct) describe the *planned* system: FastAPI, PostgreSQL, APScheduler, FullCalendar, UTC storage, a Faculty role, and day views. This file lists every section that must change so the documents describe the system **as built** on `main`.

**How to use this:**
1. Open each original document (Word/Google Docs source).
2. For each item below, replace the old text with the **New text**.
3. Change the version to 1.1 and add the revision-history row.
4. Export to PDF and replace the files in `MIni Project/Document/`.

Every claim below was checked against the code on `main` (plus PR #4) on 5 Nov 2026. Where something is **not** done or not tested, the text says so. Do not upgrade any "Not tested" or "Partial" status unless you have run the test yourself.

---

## 0. Numbers to fill in at the very end (do this last)

The test count changes as PRs merge. Before exporting the PDFs, take the final numbers from the **last green CI run on `main`** (GitHub → Actions → RLRS CI) and fill these placeholders everywhere they appear:

| Placeholder | Value now | Changes when |
|---|---|---|
| `[TOTAL]` | **68** (37 unit + 31 integration/API), after PR #4 | Lakshya's `fix/rlrs-6-11-gaps` adds 2 tests, giving 70 |
| `[CI-OS]` | Ubuntu, Windows, macOS (Python 3.12) | Only if all three CI jobs pass on `main` |
| `[UI]` | 9/9 browser steps (Playwright, Chromium, run 4–5 Nov in the build sandbox) | Re-run if UI changes |

**Time-storage decision:** pick one wording, A or B, in SRS 2.5, SAD 6.3 and SAD 11.1.
- **A (current `main`):** "Times are stored and processed in the lab's local time (Asia/Kolkata, IST); no UTC conversion is performed in this release."
- **B (only if Lakshya's `fix/rlrs-6-11-gaps` PR is merged):** "Timestamps are stored in UTC. The API, UI and emails use the lab's local time (fixed offset +05:30 by default, configurable with the `RLRS_UTC_OFFSET` environment variable). A fixed offset is used instead of a time-zone database so the app needs no extra installs on Windows."

---

## 1. All three documents: cover and revision history

**Cover page:** Version **1.1**. Date **[the day you export, e.g. 6 November 2026]**. Status **Updated to match the implemented system**.

**Authors:** replace "Four-member Software Engineering project team" with:
> Team 11: Mahipal Singh (PES1UG24AM153, team leader), Deepesh M (PES1UG24AM150), Lakshya Budhauliya (PES1UG24AM147), Venkat Kushal (PES1UG24AM124)

(Remove Venkat if he is not participating.)

**Add a revision-history row:**

| Version | Date | Author | Change summary | Approval |
|---|---|---|---|---|
| 1.1 | [export date] | Team 11 | Aligned with implemented system: Python standard-library HTTP server and SQLite instead of FastAPI/PostgreSQL; built-in worker thread instead of APScheduler; custom week calendar instead of FullCalendar; roles reduced to Student, Lab In-charge and Administrator; recorded test results and known deviations. | Pending |

**Approvals table, "Project team representative":** Name = Mahipal Singh.

---

## 2. SRS changes

### SRS 1.2 Scope: append at the end
> The submitted v1.1 build implements the scope above with the deviations listed in Section 10 (new). Faculty and Viewer roles, day calendar view, iCal, SMS, SSO and HTTPS deployment are not part of the submitted build.

### SRS 2.3 User Roles: replace the table
| Role | Needs / permissions (as implemented) |
|---|---|
| Administrator | Manage all labs, equipment, maintenance blocks, approvals and attendance; view all reservations, utilisation report and audit log. |
| Lab in-charge | Manage equipment, operating hours, slot length and booking limits **for labs they are assigned to**; approve or reject restricted bookings; create maintenance blocks; mark attendance; view reports. |
| Student | Self-register; view availability; create, view and cancel own reservations; receive emails. |

Add this sentence under the table:
> Faculty and Viewer roles from v1.0 were not implemented. Faculty can use a Student account; a read-only evaluator can use the demo accounts.

### SRS 2.4 Operating Environment: replace the paragraph
> RLRS runs in a modern desktop browser (tested with Chromium). The server is a single Python program (tested on Python 3.12 and 3.13) using only the Python standard library (`http.server`, `sqlite3`, `smtplib`, `threading`, `hashlib`), so it needs **no package installation** to run; `pytest` is needed only to run tests. Data is stored in a local SQLite file. A background worker thread inside the same process sends confirmation, cancellation and reminder emails, either through SMTP (when `SMTP_HOST` and related environment variables are set) or, by default, by writing each email as a text file into an `outbox/` folder for development and demonstration. Setup and run steps are in `MIni Project/rlrs/README.md`.

### SRS 2.5 Constraints and Assumptions: replace two bullets
- Replace "All times are stored in UTC and shown and checked in the institution's configured time zone." with **wording A or B** from Section 0.
- Replace the last bullet with: "Technologies were changed from the v1.0 plan because third-party packages could not be installed in the build environment; the deviations are recorded in Section 10."

### SRS 3.1 User Interface: replace the first bullet
> Calendar widget with a **week view** (Monday–Sunday, previous/next/this-week navigation) per equipment item, showing free, booked, own-booking and maintenance slots with text labels as well as colour. A separate day view was not implemented.

### SRS 3.2 Software Interfaces: replace the third bullet
> Emails are delivered through SMTP when configured, otherwise written to the local `outbox/` folder. Delivery through a real SMTP server has **not** been tested.

### SRS 3.3 Communications: append
> The submitted build serves plain HTTP on `127.0.0.1:8000` for local use only; HTTPS is not configured.

### SRS 4 Functional requirements: notes to add
Do not change the requirement wording (it is the agreed requirement). Instead, set the **Status** column in the SRS 9 RTM (below). These changes are needed in the acceptance criteria:
- **RLRS-F-002:** change "student, faculty, lab in-charge and administrative" to "student, lab in-charge and administrator".
- **RLRS-F-006:** change "day and week calendar views" to "a week calendar view".
- **RLRS-F-020:** change "an administrator to configure booking rules, reminder lead time and cancellation cut-off" to "a lab in-charge or administrator to configure each lab's operating hours, slot length, maximum duration, advance-booking window and maximum active bookings. Reminder lead time (2 h) and student cancellation cut-off (60 min) are fixed in this release."

### SRS 9 RTM: replace the whole table
| Req ID | Short requirement | Module (as built) | Test(s) | Status |
|---|---|---|---|---|
| RLRS-F-001 | Sign in/out | `service.login`, `server.py` | `test_register_login_and_bad_credentials`, `test_requires_login_and_session_lifecycle` | Passed (automated) |
| RLRS-F-002 | Role-based access | `service.py` role checks | `test_role_enforcement_is_server_side`, `test_student_cannot_approve` | Passed (automated) |
| RLRS-F-003 | Manage equipment | `service.create/update_equipment` | `test_equipment_management_permissions_and_search`, `test_inactive_equipment_cannot_be_booked` | Passed (automated) |
| RLRS-F-004 | Hours and slot length | `service.update_lab` | `test_lab_hours_change_drives_the_calendar_grid` | Passed (automated) |
| RLRS-F-005 | Browse/search equipment | `GET /api/equipment?q=&lab_id=&type=` | `test_equipment_management_permissions_and_search` | Partial: API search works; no search box in UI |
| RLRS-F-006 | Availability calendar | `service.availability`, `app.js` | `test_availability_marks_own_booked_and_validates_range`, UI steps 2 and 6 | Partial: week view only |
| RLRS-F-007 | Create reservation | `service.create_reservation` | `test_booking_creates_reservation_email_reminder_audit`, `test_booking_over_http_201_400_409` | Passed (automated) |
| RLRS-F-008 | Conflict detection | `rlrs_core/conflict.py` | 9 tests in `test_conflict.py`, `test_conflict_returns_409_with_range_and_rolls_back` | Passed (automated) |
| RLRS-F-009 | Booking rules | `rlrs_core/rules.py` | 10 tests in `test_rules.py`, `test_rule_violations_return_400_with_codes` | Passed (automated) |
| RLRS-F-010 | Approval flow | `service.approve/reject_reservation` | `test_approval_flow_and_rejection`, `test_approval_flow_over_http` | Passed (automated) |
| RLRS-F-011 | My reservations | `GET /api/reservations/mine` | UI step 4 | Passed (browser test) |
| RLRS-F-012 | Cancel reservation | `service.cancel_reservation` | `test_cancel_frees_slot_and_cancels_reminder`, `test_cancel_after_cutoff_refused` | Passed (automated) |
| RLRS-F-013 | Maintenance block | `rlrs_core/maintenance.py`, `service.add_maintenance` | `test_maintenance_cancels_overlapping_and_blocks_new_bookings`, 2 unit tests, UI step 5 | Passed (automated) |
| RLRS-F-014 | Event emails | `service._email`, `mailer.py` | `test_booking_creates_reservation_email_reminder_audit`, `test_emails_flushed_once_and_retried_on_failure` | Passed to outbox; real SMTP not tested |
| RLRS-F-015 | Reminder email | `rlrs_core/reminders.py`, worker | `test_reminder_sent_two_hours_before_exactly_once_and_survives_restart`, `test_no_reminder_after_cancellation`, 9 unit tests | Passed (automated) |
| RLRS-F-016 | Retry failed emails | worker in `server.py`, `reminders.py` | `test_temporary_failure_is_retried_then_succeeds`, `test_repeated_failure_marks_failed` | Passed (automated) |
| RLRS-F-017 | Remote-access info for holder only | `equipment.remote_info` | none | **Not met:** remote-access text is currently shown to every signed-in user |
| RLRS-F-018 | Attendance | `rlrs_core/attendance.py` | `test_attendance_only_after_slot_end_and_audited`, 3 unit tests | Passed (automated) |
| RLRS-F-019 | Utilisation report | `rlrs_core/report.py` | `test_utilisation_report_reconciles`, 3 unit tests, UI step 7 | Passed (automated) |
| RLRS-F-020 | Configure rules | `PUT /api/labs/{id}` | `test_lab_hours_change_drives_the_calendar_grid` | Partial: per-lab rules editable; lead time and cut-off fixed |
| RLRS-F-021 | Audit log | `rlrs_core/audit.py` | `test_audit_records_actor_action_time_and_redacts_secrets`, `test_audit_never_contains_password` | Passed (automated) |
| RLRS-F-022 | Safe errors | `server.py` error handler | `test_errors_are_json_without_stack_traces` | Passed (automated) |
| RLRS-NF-001 | Performance (20k reservations) | n/a | none | **Not tested** |
| RLRS-NF-002 | No double booking | `BEGIN IMMEDIATE` transaction | `test_concurrent_requests_for_same_slot_yield_exactly_one_booking` (10 parallel requests, exactly 1 succeeds) | Passed (automated) |
| RLRS-NF-003 | Survive restart, reminders once | SQLite + reminder_jobs | `test_reminder_sent_two_hours_before_exactly_once_and_survives_restart` | Passed (automated) |
| RLRS-NF-004 | Reminder within 5 min | worker every 30 s | covered by reminder tests (fake clock) | Passed (automated, fake clock) |
| RLRS-NF-005 | Secure credentials | `security.py` (PBKDF2) | `test_audit_never_contains_password`, `test_cookie_is_httponly` | Passed (automated) |
| RLRS-NF-006 | Usability checklist | UI | UI steps 1–9 | Partial: no formal checklist run |
| RLRS-NF-007 | Engine testable alone | `rlrs_core/` (no I/O) | 37 unit tests | Passed (automated) |
| RLRS-NF-008 | Documented setup | README | CI on `[CI-OS]` | Passed in CI; manual run by each member: [fill in] |
| RLRS-SR-001/002 | AuthN/AuthZ server-side | `service.py` | `test_role_enforcement_is_server_side` | Passed (automated) |
| RLRS-SR-003 | Salted hashing | `security.py` | `test_audit_never_contains_password` | Passed (automated) |
| RLRS-SR-004 | Input validation | `server.py`, `service.py` | `test_sql_injection_strings_are_inert`, `test_rule_violations_return_400_with_codes` | Passed (automated) |
| RLRS-SR-005 | Record-level access | `service.cancel_reservation`, lab staff check | `test_student_cannot_cancel_someone_elses_reservation`, `test_cancel_over_http_and_other_user_forbidden` | Partial: cancel protected; remote-access info not restricted (see F-017); cross-lab in-charge test only on Lakshya's branch |
| RLRS-SR-006 | Secrets via env vars | `mailer.py` | inspection | Passed (inspection: SMTP settings read from environment, none in repo) |
| RLRS-SR-007 | Audit without secrets | `rlrs_core/audit.py` | `test_audit_records_actor_action_time_and_redacts_secrets` | Passed (automated) |

### SRS: add a new Section 10, "Deviations from v1.0"
| Area | v1.0 plan | v1.1 as built | Reason |
|---|---|---|---|
| Web framework | FastAPI/Flask | Python standard-library `http.server` | Package index blocked in build environment; zero-install also simplifies team setup |
| Database | PostgreSQL (SQLite for dev) | SQLite only | Same reason; concurrency handled with `BEGIN IMMEDIATE` transactions |
| Job scheduler | APScheduler/Celery beat | Background thread in the server, every 30 s | No third-party packages |
| Calendar | FullCalendar, day + week | Custom HTML/JS week grid | No third-party packages; day view dropped for time |
| Roles | Admin, Lab in-charge, Faculty, Student, Viewer | Admin, Lab in-charge, Student | Scope reduction |
| Time storage | UTC | Wording A or B from Section 0 | `zoneinfo` needs an extra package on Windows |
| Email in dev | Mailpit | Text files in `outbox/` | No extra software needed for the demo |
| Remote-access visibility (F-017) | Holder only | Visible to all signed-in users | Not implemented; known gap |
| Security | HTTPS, rate limiting | Not implemented (local demo only) | Out of time; documented as risk |

---

## 3. SAD changes

### SAD 4.1 Chosen Pattern: replace the second and third sentences
> A background worker thread, started by the same server process, sends due reminders and queued emails every 30 seconds. This keeps the system to a single program while still separating time-based work from request handling.

### SAD 4.2 Component Responsibilities: replace the "Key interactions" column with actual modules
| Component | Implemented in |
|---|---|
| Front end / calendar UI | `rlrs_app/static/index.html`, `app.js`, `style.css` (week view) |
| REST API layer | `rlrs_app/server.py` (`ROUTES` table, JSON errors, 1 MB body limit, static files) |
| Authentication / authorization | `rlrs_app/security.py` (PBKDF2-SHA256, 120,000 iterations), sessions table, role checks in `service.py` |
| Lab & equipment service | `service.update_lab`, `create_equipment`, `update_equipment`, `list_equipment` |
| Availability service | `service.availability` |
| Scheduling engine | `rlrs_core/conflict.py`, `rlrs_core/rules.py` (pure logic, no I/O) |
| Reservation service | `service.create_reservation`, `cancel_`, `approve_`, `reject_`, `mark_reservation_attendance` |
| Notification service | `service._email` (queues rows in `email_jobs`), `rlrs_core/reminders.py` |
| Job worker | worker thread in `server.py`; sends through `mailer.py` (`SmtpTransport` or `FileTransport`) |
| Reporting service | `rlrs_core/report.py`, `service.utilisation` |
| Audit service | `rlrs_core/audit.py` (redaction), `service._audit` |
| Data-access layer | `rlrs_app/db.py` (schema), SQL inside `service.py`, all parameterised |
| Database | SQLite file (`rlrs.db`) |

### SAD 4.3 Component diagram
Keep the text and add: "Job Worker runs as a thread in the server process." If you add an image, render `docs/diagrams/05_component.puml` (paste it into https://www.plantuml.com/plantuml) and check it matches the table above.

### SAD 5: replace the whole first paragraph
> The implemented stack is: **Python standard library only** (tested on Python 3.12 and 3.13): `http.server` (threaded) for the REST API and static files, `sqlite3` for persistence, `threading` for the background email/reminder worker, `smtplib` for SMTP, and `hashlib.pbkdf2_hmac` for passwords. The front end is plain HTML, CSS and JavaScript with a custom week-view calendar grid. Tests use `pytest` (unit and integration) and Playwright with Chromium (browser smoke test). This replaces the v1.0 proposal (FastAPI, PostgreSQL, APScheduler, FullCalendar, Mailpit) because the build environment could not install third-party packages. The standard-library approach also means team members can run the app with no installation steps.

Replace the second paragraph with:
> Development tooling: Git/GitHub feature branches and pull requests; GitHub Actions (`.github/workflows/rlrs-ci.yml`) runs `pytest` on `[CI-OS]` for every pull request and push to `main`; Jira (project RLRS) for stories and sprints.

### SAD 6 Data Design: replace the table
| Table | Fields (as built) | Rules |
|---|---|---|
| users | id, name, email (unique), role (Student / LabInCharge / Admin), pw_hash | Role stored on user; no separate Role table |
| sessions | token, user_id, expires | 8-hour sessions; HttpOnly, SameSite=Lax cookie |
| labs | id, name, incharge_id, open_time, close_time, slot_minutes, max_duration, advance_days, max_active | Booking rules stored per lab (defaults 09:00–18:00, 30 min, 120 min, 14 days, 3 active) |
| equipment | id, lab_id, name, type, description, requires_approval, active, remote_info | Inactive equipment cannot be booked |
| reservations | id, user_id, equipment_id, start_ts, end_ts, status, created_at, reason | Status ∈ Pending, Confirmed, Cancelled, Rejected, Completed, NoShow |
| maintenance | id, equipment_id, start_ts, end_ts, reason | Overlapping Pending/Confirmed reservations cancelled on creation |
| reminder_jobs | id, reservation_id (unique), send_at, status, attempts, next_attempt_at | Unique per reservation, so each reminder is sent once |
| email_jobs | id, to_email, subject, body, status, attempts, next_attempt_at, created_at | Up to 3 attempts, 5-minute backoff, then Failed |
| audit | id, actor, action, at, details (JSON) | Append-only; password/token/secret keys redacted |

### SAD 6.1: replace the last paragraph
> The rule checks, final overlap check, insert, and creation of the email job, reminder job and audit entry all run inside **one SQLite `BEGIN IMMEDIATE` transaction**, which takes the database write lock before reading. A second concurrent request waits for the lock and then sees the first booking, so it is rejected with 409. This is verified by an automated test that sends 10 parallel requests for the same slot and checks that exactly 1 succeeds. (PostgreSQL exclusion constraints were not used because PostgreSQL is not part of the build.)

### SAD 6.2 State model
Rename "No-show" to "NoShow" to match the code. Add a note: "Students cannot cancel within 60 minutes of the start time; lab in-charges and administrators can cancel at any time."

### SAD 6.3: replace the second bullet
Use **wording A or B** from Section 0.

### SAD 7 API: replace the table
| Operation | Method / route | Auth | Result |
|---|---|---|---|
| Health check | `GET /api/health` | none | 200 `{status, db, time}` |
| Register / login / logout | `POST /api/register`, `/api/login`, `/api/logout` | none | 201 / 200 + cookie / 200; 401 bad credentials |
| Current user | `GET /api/me` | login | 200; 401 |
| List labs / update lab rules | `GET /api/labs`; `PUT /api/labs/{id}` | login; lab staff | 200; 400; 403 |
| List / search equipment | `GET /api/equipment?lab_id=&type=&q=` | login | 200 (students see active only) |
| Create / update equipment | `POST /api/equipment`; `PUT /api/equipment/{id}` | lab staff | 201 / 200; 400; 403 |
| Availability | `GET /api/equipment/{id}/availability?from=&to=` | login | slot list with state; 400 invalid range |
| Create reservation | `POST /api/reservations` `{equipment_id, start, end}` | login | 201 Confirmed/Pending; 400 rule codes; 409 conflict with range |
| My reservations | `GET /api/reservations/mine` | login | 200 |
| Staff reservation list | `GET /api/reservations/manage?status=` | lab staff | 200 |
| Cancel | `POST /api/reservations/{id}/cancel` | owner or lab staff | 200; 403; 409 past cut-off |
| Approve / reject | `POST /api/reservations/{id}/approve`, `/reject {reason}` | lab staff | 200; 400 missing reason; 403; 409 |
| Attendance | `POST /api/reservations/{id}/attendance {outcome}` | lab staff | 200; 409 slot not finished |
| Maintenance block | `POST /api/maintenance {equipment_id, start, end, reason}` | lab staff | 201; affected reservations cancelled and emailed |
| Utilisation report | `GET /api/reports/utilisation?from=&to=` | lab staff | 200 |
| Audit log | `GET /api/audit` | lab staff | 200 |

All errors are JSON `{error, message, details}` with no stack traces.

### SAD 8.2 Send Reminder: replace the first bullet
> The worker thread runs every 30 seconds (configurable with `--worker-interval`) and selects reminder and email jobs that are Pending and due.

### SAD 9 Security: add a status column
| Threat | Status in v1.1 |
|---|---|
| Unauthorized access | Done: login required; server-side role checks |
| Acting on someone else's booking | Done for cancel/approve; **remote-access info not restricted** |
| Double booking | Done: `BEGIN IMMEDIATE` transaction, concurrency test |
| Credential disclosure | Done: PBKDF2-SHA256 salted hashes, HttpOnly cookie, SMTP settings from environment. **HTTPS not configured** |
| Injection / XSS | Done: parameterised SQL; UI uses `textContent` (no `innerHTML`); path traversal blocked |
| Privilege escalation | Done: tested by `test_role_enforcement_is_server_side` |
| Abuse of endpoints | Partial: 1 MB body limit, active-booking limit; **no login rate limiting, no CSRF tokens** (SameSite=Lax cookie only) |

### SAD 11.1 Risks: replace the "time-zone" row mitigation
> Half-open ranges and boundary tests (back-to-back, operating-hour edges, advance-window edge); time storage per wording A or B in Section 0.

### SAD 11.2 Open Issues: replace the whole list
- Resolved: final framework, database, calendar and scheduler are recorded in Section 5.
- Resolved: default booking rules are 09:00–18:00, 30-min slots, max 120 min, 14 days ahead, 3 active per user, 60-min student cancellation cut-off, reminder 2 h before.
- Open: remote-access information is visible to all users (RLRS-F-017).
- Open: performance target RLRS-NF-001 not measured.
- Open: real SMTP delivery not tested.
- Out of scope for this release: Faculty role, waitlist, day calendar view, HTTPS.

---

## 4. Test Plan changes

### TP 6 Test Environment: replace the "Software" and "Tools" rows
| Area | Plan (as executed) |
|---|---|
| Software | Python 3.12 (CI) / 3.13 (build sandbox); standard library only; SQLite |
| Browser | Chromium (via Playwright) |
| Tools | pytest; a fake clock passed into every service function (no freezegun needed); `FileTransport` writing emails to a temp folder instead of Mailpit; a stub transport that raises errors to simulate SMTP failure; Playwright for the browser smoke test; GitHub Actions on `[CI-OS]`; Jira for defects/stories |
| Test data | `rlrs_app/seed.py`: 4 users (2 students, 1 lab in-charge, 1 admin, all `@lab.test`), 2 labs (Electronics, Fabrication) with 3 equipment items, one of which (3D Printer) requires approval. The 200-equipment / 20,000-reservation performance dataset was **not built**. |

### TP 7 Test Schedule: replace the table
| Activity | Planned | Actual |
|---|---|---|
| Review SRS/SAD, prepare cases | Sprint 1 | Done: test case list in this plan |
| Unit tests (scheduling engine) | Sprint 1 (27–31 Oct) | 37 unit tests written and passing on 31 Oct (`docs/test_evidence_unit_2026-10-31.txt`). No application stories were completed in Sprint 1. |
| Integration, API, concurrency, reminder, report tests | Sprint 2 (2–7 Nov) | `[TOTAL]` automated tests passing by 5 Nov (`docs/test_evidence_2026-11-05.txt` and CI) |
| Browser end-to-end | Sprint 2 | 9/9 steps passing (Playwright) |
| Final acceptance run and evidence | By 7 Nov | [fill in after each owner verifies their stories] |
| Demo readiness | From 9 Nov | [fill in] |

### TP 9 Roles and Responsibilities: replace "fill in name" rows
| Role | Assigned person | Responsibilities |
|---|---|---|
| Test coordinator / QA, notifications, CI, documentation | Mahipal Singh | RTM, CI, reminder/email/maintenance/attendance/report tests, evidence, documents |
| Scheduling engine / backend | Lakshya Budhauliya | Conflict, booking-rule, reservation API and approval tests |
| Calendar UI / API | Deepesh M | Sign-in, equipment, calendar, booking form and email tests; macOS run |
| [Role] | Venkat Kushal | [fill in, or remove the row] |

### TP 13: add an "Automated test" and "Result" column
| Test case | Automated test(s) | Result |
|---|---|---|
| TC-AUTH-01 | `test_register_login_and_bad_credentials`, `test_requires_login_and_session_lifecycle` | Pass |
| TC-AUTH-02 | `test_role_enforcement_is_server_side` | Pass |
| TC-EQ-01 | `test_equipment_management_permissions_and_search` | Pass |
| TC-EQ-02 | `test_inactive_equipment_cannot_be_booked` | Pass |
| TC-CAL-01 | `test_availability_marks_own_booked_and_validates_range`; UI step 6 | Pass (week view) |
| TC-BOOK-01 | `test_booking_creates_reservation_email_reminder_audit`, `test_booking_over_http_201_400_409` | Pass |
| TC-CONF-01 | `test_partial_overlap_rejected_with_range`, `test_conflict_returns_409_with_range_and_rolls_back` | Pass |
| TC-CONF-02 | `test_touching_back_to_back_is_accepted` | Pass |
| TC-CONF-03 | `test_containing_and_contained_rejected` | Pass |
| TC-CONF-04 | `test_cancelled_slot_can_be_rebooked` | Pass |
| TC-RULE-01 | `test_past_start`, `test_outside_hours_boundaries` | Pass |
| TC-RULE-02 | `test_advance_window_edge`, `test_max_duration_edge` | Pass |
| TC-RULE-03 | `test_max_active_per_user` | Pass |
| TC-RULE-04 | `test_user_cannot_double_book_same_time_on_other_equipment` | Pass |
| TC-APPR-01 | `test_approval_flow_and_rejection`, `test_approval_flow_over_http` | Pass |
| TC-CANC-01 | `test_cancel_frees_slot_and_cancels_reminder` | Pass |
| TC-CANC-02 | `test_cancel_after_cutoff_refused` | Pass |
| TC-MAINT-01 | `test_maintenance_cancels_overlapping_and_blocks_new_bookings`; UI step 5 | Pass |
| TC-MAIL-01 | `test_emails_flushed_once_and_retried_on_failure`, `test_repeated_failure_marks_failed` | Pass (simulated SMTP failure) |
| TC-MAIL-02 | `test_sent_exactly_once_even_if_worker_runs_twice`, `test_reminder_sent_two_hours_before_exactly_once_and_survives_restart` | Pass |
| TC-MAIL-03 | `test_no_reminder_after_cancellation` | Pass |
| TC-ATT-01 | `test_attendance_only_after_slot_end_and_audited`, `test_mark_completed_and_no_show_after_end` | Pass |
| TC-REP-01 | `test_utilisation_report_reconciles`, `test_known_dataset_reconciles` | Pass |
| TC-AUDIT-01 | `test_audit_records_actor_action_time_and_redacts_secrets`, `test_audit_never_contains_password` | Pass |
| TC-CONC-01 | `test_concurrent_requests_for_same_slot_yield_exactly_one_booking` | Pass |
| TC-PERF-01 | none | **Not run** |
| TC-RESTART-01 | `test_reminder_sent_two_hours_before_exactly_once_and_survives_restart` | Pass |
| TC-SEC-01 | `test_audit_never_contains_password`, `test_cookie_is_httponly`; repo inspection | Pass |
| TC-SEC-02 | `test_student_cannot_cancel_someone_elses_reservation`, `test_cancel_over_http_and_other_user_forbidden` | **Partial**: cancel part passes; remote-access part fails (info visible to all) |

Add new rows:
| Test case | Scenario | Expected | Automated test | Result |
|---|---|---|---|---|
| TC-HEALTH-01 | `GET /api/health` without login | 200, `status` ok, `db` ok | `test_health_endpoint_is_public_and_checks_db` | Pass |
| TC-SEC-03 | SQL-injection strings in inputs | Treated as plain text; no error, no data change | `test_sql_injection_strings_are_inert` | Pass |
| TC-SEC-04 | Request `/../` paths for static files | 404; no file outside `static/` served | `test_static_page_served_and_path_traversal_blocked` | Pass |
| TC-ERR-01 | Trigger errors | JSON error, no stack trace | `test_errors_are_json_without_stack_traces` | Pass |

### TP 14: add a "Results summary" paragraph
> **Results as of [export date]:** `[TOTAL]` automated tests executed, `[TOTAL]` passed, 0 failed (pytest, Linux; CI on `[CI-OS]`). Browser smoke test: 9/9 steps passed. Test cases planned: 29 (+4 added) = 33; executed: 32; passed: 31; partial: 1 (TC-SEC-02); not run: 1 (TC-PERF-01). Double-booking incidents: 0. Duplicate or missed reminders: 0. Tests were mutation-checked: 5 deliberate bugs were introduced and each was caught by at least one test. Open defects: remote-access info visible to all users (affects F-017 / SR-005).

*Check the counts above before exporting:* 29 original cases + 4 new = 33. TC-PERF-01 is not run, so 32 executed. TC-SEC-02 is partial, so 31 fully passed.

---

## 5. What is still not true (do not claim these in the presentation)
- The app has not been run by a team member on their own Windows or macOS machine (CI covers this once all three jobs are green).
- Real SMTP email has not been sent.
- Performance (NF-001) has not been measured.
- `.puml` diagrams have never been rendered; render them and check they match the code before putting them in the SAD.
- Remote-access info is not restricted to the reservation holder.

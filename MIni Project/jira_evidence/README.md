# Jira evidence (RLRS, Team 11)

Project: Remote Lab Reservation System. Jira project key `RLRS`, board 36.

| File | Shows |
|---|---|
| `01_jira_dashboard.png` | Dashboard: status, story points per assignee, points completed per day |
| `02_product_backlog.png` | Product backlog: 15 stories (74 pts) + 4 Sprint 1 task records |
| `03_sprint1_backlog.png` | Sprint 1 - Foundation (27-31 Oct), closed |
| `04_sprint2_backlog.png` | Sprint 2 - Build and Test (2-7 Nov) |
| `05_burndown_sprint1.png` | Burndown, Sprint 1 |
| `06_burndown_sprint2.png` | Burndown, Sprint 2 |
| `07_sprint_progress.png` | Sprint progress |

## Real Jira screenshots (`screenshots/`)
Taken from the Jira web UI on 17 Nov 2026.

| File | Shows |
|---|---|
| `01_board_after_sprints_closed.png`, `02_backlog_after_sprints_closed.png` | Board and Backlog. They look empty because both sprints are completed in Jira and every work item is Done |
| `03_reports_status_type_assignee.png`, `04_reports_trends.png` | Reports: status, type, assignee, creation trend, cycle time |
| `05_summary_status_overview.png`, `06_summary_priority_types.png` | Project Summary: 19 of 19 work items Done |
| `07_burndown_sprint2_jira.png` | Jira burndown, Sprint 2 (74 pts, work completed 5 Nov and 11 Nov) |
| `08_burndown_sprint1_jira.png` | Jira burndown, Sprint 1 (26 pts committed, none burned down) |
| `09_sprint1_report_scope_changes.png`, `10_sprint1_report_incomplete_items.png` | Jira Sprint 1 report: scope log and the 5 stories carried over (now Done) |

## How the numbered images below were made (please read)
These images were **rendered from the Jira API data (issue fields and change history) on 17 Nov 2026**, not captured from the Jira web UI. Each image says so in its footer. `generate_images.py` holds the exact data and the code.

## What the data shows (no spin)
- Sprint 1 committed 26 pts (RLRS-1..5). None were Done when the sprint was closed on 31 Oct; all five carried into Sprint 2.
- Sprint 2 scope was 74 pts. 22 pts were marked Done on 5 Nov and the other 52 pts on 11 Nov, **after** the planned sprint end (7 Nov). The burndown therefore shows the work finishing late.
- Sprint 2 was completed (closed) in Jira on 17 Nov 2026, after the planned end of 7 Nov.

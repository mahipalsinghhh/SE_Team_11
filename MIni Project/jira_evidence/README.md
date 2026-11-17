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

## How these were made (please read)
These images were **rendered from the Jira API data (issue fields and change history) on 17 Nov 2026**, not captured from the Jira web UI. Each image says so in its footer. `generate_images.py` holds the exact data and the code.

## What the data shows (no spin)
- Sprint 1 committed 26 pts (RLRS-1..5). None were Done when the sprint was closed on 31 Oct; all five carried into Sprint 2.
- Sprint 2 scope was 74 pts. 22 pts were marked Done on 5 Nov and the other 52 pts on 11 Nov, **after** the planned sprint end (7 Nov). The burndown therefore shows the work finishing late.
- Sprint 2 was never formally closed in Jira (its state is still "active").

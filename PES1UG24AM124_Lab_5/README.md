# Lab 5: static code analysis

Venkat Kushal | PES1UG24AM124

Bike-share station manager. This version retains the station operations but uses an atomic rental update, explicit error propagation and an import-safe demonstration.

## Run

```sh
python -m pip install -r requirements.txt
python bike_share_stations.py
python -m pytest -q
python -m pylint --persistent=no bike_share_stations.py
python -m bandit -r bike_share_stations.py
python -m flake8 bike_share_stations.py
```

The database is in memory, so each process starts empty. Scan only the submitted application module when reproducing the reported scores. The tests deliberately contain assertions.

## Files

- bike_share_stations.py: cleaned application.
- test_bike_share_stations.py: seven regression tests.
- issues.md: seven issue groups and their fixes.
- reflection.md: four fresh reflection answers.
- evidence/: fresh logs and a readable run-evidence image.
- source_reports_before/: attributed historical baseline reports, not new runs.
- Lab_5_Report.pdf: formatted issue record and reflections.
- SOURCES.md: provenance and handout limitation.

Result: 7 tests pass; Pylint 10.00/10; Bandit and Flake8 report no findings on the application module. Review the reflection answers and handout before submission.

# Lab 6: statement and branch coverage

Venkat Kushal | PES1UG24AM124

## Reproduce

```sh
python -m pip install -r requirements.txt
python -m pytest -q
python -m coverage run --source=shopping_cart -m pytest CodeCoverageTest_shopping_cart.py -q
python -m coverage report -m
python -m coverage run --branch --source=shopping_cart -m pytest BranchCoverageTest_shopping_cart.py -q
python -m coverage report -m
python -m coverage html
```

pytest.ini includes the required capitalized suite filenames in normal discovery. Without that setting, a bare pytest invocation would skip them.

## Included

- shopping_cart.py: lightly reorganized application, with original APIs and rules.
- CodeCoverageTest_shopping_cart.py: 14 statement-coverage cases.
- BranchCoverageTest_shopping_cart.py: 25 branch and boundary cases.
- test_shopping_cart.py: two smoke cases.
- coverage_notes.md and Lab_6_Report.pdf: explanation and measured results.
- evidence/: logs, run-evidence images and an offline HTML coverage report.
- preparation_history.bundle: a portable repository with three commits.

Restore history in a new folder:

```sh
git clone preparation_history.bundle Lab6-history
```

Result: 41 tests passed; isolated statement and branch suites both report 100% on shopping_cart.py. No repository was uploaded or altered as part of creating this package. See SOURCES.md before submission.

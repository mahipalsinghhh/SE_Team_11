# Lab 7: property-based fuzz testing

Venkat Kushal | PES1UG24AM124

## Run the repaired code

```sh
python -m pip install -r requirements.txt
python -m pytest test_shopping_cart.py -q --tb=short
python shopping_cart.py
```

## Reproduce the baseline comparison

Create a separate scratch folder, copy shopping_cart_before.py into it as shopping_cart.py, and copy test_shopping_cart.py beside it. Run the same pytest command in that folder. Do not overwrite the fixed file in this submission. The baseline intentionally fails.

## Files

- shopping_cart_before.py: unchanged original teaching source.
- shopping_cart.py: repaired parsers and guarded command-line demonstration.
- test_shopping_cart.py: 7 generated properties plus 19 parameterized regressions, 26 collected cases.
- bugs_found.md: observed failures, input contract and repairs.
- reflection.md: four rewritten answers.
- evidence/: fresh before/after logs and readable evidence images.
- Lab_7_Report.pdf: failure analysis and reflection answers.

Measured result: baseline 18 failed / 8 passed; repaired 26 passed. The new suite is broader than the source submission, so its counts differ. Generated no-crash properties use reproducible settings; this is a bounded test run, not a proof over every possible input. See SOURCES.md for provenance and the handout limitation.

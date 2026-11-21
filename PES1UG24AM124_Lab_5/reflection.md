# Lab 5: reflection answers

Venkat Kushal | PES1UG24AM124

## What does static analysis add to running a program?

A successful demonstration only checks the operations and data used in that demonstration. Static tools inspect patterns across the source, so they can point out a shared default list or unsafe SQL even when ordinary output looks reasonable. I would treat their findings as a review checklist, then use tests to check the actual behaviour.

## Which findings matter most here?

The SQL construction and missing-record path deserve attention before cosmetic warnings. The former confuses data with executable SQL; the latter fails when a station number is absent. The default list is another important case because its effect appears across separate calls. A regression test is needed to make that hidden state visible.

## How do the three tools differ?

Bandit focuses on patterns associated with security problems, such as weak credential randomness and SQL construction. Pylint also examines naming, documentation and suspicious program structure, including inconsistent returns. Flake8 is useful for compact style and unused-name feedback. Their overlap is useful, but their reports need interpretation: a low-severity Bandit finding can still describe a behaviour worth fixing.

## How would this change a future workflow?

I would run the scans before review and keep behaviour tests alongside the fixes. The tests in this package check what the warnings alone cannot establish, such as safe storage of an apostrophe and correct results for an empty station. A clean scan is a starting point for review, not a reason to stop testing.

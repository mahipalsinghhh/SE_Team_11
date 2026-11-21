# Lab 6: coverage notes

Venkat Kushal | PES1UG24AM124

## Statement suite

CodeCoverageTest_shopping_cart.py has 14 parameterized cases. It executes the category validation, both invalid numeric conditions, tax arithmetic, bulk reduction, each discount tier, membership and coupon additions, and ordinary/express delivery. The run executes all 33 statements in shopping_cart.py.

## Branch suite

BranchCoverageTest_shopping_cart.py has 25 cases. Quantity 9/10/11 checks the bulk boundary, while cart values 1999/2000 and 4999/5000 check tier changes. Coupon cases distinguish the wrong code, a matching code below 1000 and an eligible code. Delivery cases cover both membership values, the 499/500 boundary and express/non-express paths. Invalid price and invalid quantity cases separately exercise the short-circuit OR operands.

The isolated branch run executes all 33 statements and all 22 measured branch destinations, with no partial branches: 100% in coverage.py. coverage.py's branch metric measures control-flow arcs, not full condition coverage or MC/DC. The extra condition-focused cases are listed explicitly rather than claiming the tool proves those stronger metrics.

## Arithmetic check

At price 100 and quantity 11, the bulk subtotal is 1100 - 110 = 990. Food GST is 990 * 5 // 100 = 49, so the expected result is 1039. Integer truncation is preserved from the starter rather than silently replaced with rounding.

## What the result means

The complete run contains 41 passing cases: 14 statement, 25 branch and 2 smoke cases. Full coverage means the measured application paths ran. It does not guarantee correct requirements, exclude every numerical edge case or replace fuzz testing. The public function signatures and the original integer-arithmetic rules are unchanged.

## Local commit history

A Git bundle includes three real preparation commits: application setup, statement tests, then branch tests and evidence. These commits record package preparation; they are not attributed to Venkat personally. Clone it with the command in README.md if a repository with history is required.

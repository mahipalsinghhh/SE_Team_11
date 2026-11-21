# Lab 7: reflection answers

Venkat Kushal | PES1UG24AM124

## What is useful about fuzz testing?

The important part is testing a rule over a large input space rather than writing many near-identical examples. Here the rule is that an input is either parsed successfully or rejected with ValueError. Hypothesis explores values I have not listed by hand and reduces unexpected failures to inputs that are easier to understand.

## Which defects are most informative?

An empty pincode exposes indexing before validation, while a one-digit pincode exposes a different problem: the function can return a believable but invalid answer. The offer OFF250 has the same silent-failure pattern. Testing the range of successful results is therefore as important as checking whether an exception occurred.

## How does this complement coverage testing?

The Lab 6 suites target known decisions and thresholds in arithmetic. They are useful when the expected result is specified precisely. Generated parser inputs explore malformed structure and unexpected types. A line may have been executed many times and still fail on a new type or delimiter arrangement, so a coverage percentage cannot stand in for these properties.

## Where would this be useful next?

I would apply this approach to request parsers and configuration readers. First I would define valid inputs and accepted rejection errors. Then I would combine generated valid data, broad invalid data and saved regression examples. Restricting the accepted error type matters because catching every exception inside a test would hide the defects the test is supposed to reveal.

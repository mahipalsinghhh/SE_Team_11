# Lab 7: failure analysis

Venkat Kushal | PES1UG24AM124

The exact same completed test suite was run against the original teaching source and the validated module. The baseline run has 18 failing and 8 passing cases. The fixed run has 26 passing cases. Each parameterized row counts as a case; a generated property can test many inputs within one case.

| Function | Input or property | Baseline problem | Repair |
|---|---|---|---|
| cart_total | None | AttributeError before parsing starts | Reject non-text values explicitly. |
| cart_total | Missing separators or extra separators | Parsing assumes every split has exactly two parts | Match a complete item structure before conversion. |
| cart_total | Negative price or quantity; blank item name | Bad values can be accepted silently | Require ASCII non-negative integer fields and a nonblank name. Zero quantity remains allowed because the starter has no positive-only rule. |
| promo_percent | Empty string, None or bytes | IndexError, AttributeError or TypeError from unconditional string operations | Validate the type, then match the whole normalized offer. |
| promo_percent | OFF101, OFF250 or OFF-1 | Values outside the percentage range are returned | Check the inclusive range 0 to 100. |
| promo_percent | XOFF20 | Extra prefix is accepted | Use fullmatch rather than searching for a substring. |
| delivery_zone | Empty input, None or unsupported prefix 0 | IndexError, TypeError or KeyError escapes | Validate type and shape, then reject an unmapped prefix with ValueError. |
| delivery_zone | One/five/seven digits | The first character alone chooses a region | Require exactly six ASCII digits before lookup. |
| delivery_zone | Non-ASCII numeric characters | A numeric-looking prefix is not a configured dictionary key | Make the accepted character set explicit with [0-9]. |

The first three no-crash properties each generate 300 examples, including text, None, integers, bytes and short lists. Structured cart generation tests the sum with an independent oracle. Other properties check normalized offers and known/unknown postal prefixes. Fixed regressions keep previously exposed examples in the suite.

Only ValueError is accepted as intentional input rejection. Unexpected exceptions still fail the no-crash tests. The baseline raw log contains the actual reduced Hypothesis examples, including None, empty text, empty bytes and prefix 0; no screenshot from another submission was reused.

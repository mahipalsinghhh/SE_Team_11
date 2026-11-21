# Lab 5: issue and fix record

Venkat Kushal | PES1UG24AM124

The baseline locations below refer to the inherited reports, not to the reformatted final file. Severity labels distinguish security-tool severity from behavioural risk.

| Issue | Type / severity | Baseline line(s) | Explanation | Change in this version |
|---|---|---|---|---|
| SQL assembled from values | Security, Bandit Medium (B608) | 9 | A station name becomes part of the SQL syntax. Even an apostrophe can break an insertion. | Pass the three values separately to SQLite placeholders. |
| Shared list default | Correctness risk (W0102) | 8 | Calls without a log reuse one list, linking otherwise separate operations. | Select a fresh list when the argument is None; preserve a supplied list. |
| Indexing an absent record | Correctness risk; None comparison warnings C0121/E711 | 38-40 | A lookup can return None, which cannot be indexed. The comparison warning points near, but does not itself prove, this runtime bug. | Check the complete record before reading its bike count. |
| General-purpose PIN randomness | Security, Bandit Low (B311) | 21-22 | A normal pseudo-random stream is a poor choice for access credentials. | Generate the four-digit value with secrets.randbelow. |
| Errors discarded | Security, Bandit Low (B110); quality W0718 | 31-35 | A failed reset looks the same as a successful reset because the exception is ignored. | Remove the catch-all handler, allowing the caller to handle sqlite3 errors. |
| Ambiguous rental result | Quality / API consistency (R1710) | 14-19 | The two paths return different kinds of result. | Return a Boolean based on the conditional update's affected row count. |
| Dead assignment and inconsistent style | Quality (W0612/F841 and style checks) | 27 and multiple locations | Unused values add noise; long statements and undocumented functions slow review. | Remove the dead value, use descriptive names and document each operation. |

## Additional structural change

Rental uses one UPDATE guarded by bikes > 0 instead of a separate SELECT followed by UPDATE. This removes the read/update gap within that operation and preserves the behaviour for missing or empty stations. Importing the module no longer runs its demonstration.

## Fresh validation

- Pylint: 10.00/10 on the submitted station module.
- Bandit: no issues identified in that module.
- Flake8: no findings in that module.
- pytest: 7 behavioural tests passed, including independent logs, apostrophes, missing records, empty stock, reset, PIN range and visible database errors.

The inherited baseline reports show 3.89/10, three Bandit findings and ten Flake8 findings. These are historical source results, not new measurements. Static scans do not establish that the entire program is secure.

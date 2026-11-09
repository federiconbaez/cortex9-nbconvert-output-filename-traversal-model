# Sources

Local copies under `security-research-45/sources/cve2026/` (not in this
repo). Each SHA-256 was checked against `sources/cve2026/SHA256SUMS` before
use. Diff line numbers in this repo refer to the saved diff.

| Source | URL | Commit | SHA-256 of copy |
|---|---|---|---|
| Fix diff `diffs/CVE-2026-114140_nbconvert_ce4bd99aec31.diff` (2 files, +38/-1) | https://github.com/jupyter/nbconvert/commit/ce4bd99aec31d81d759fa8eeb8643179392ec66f | ce4bd99aec31d81d759fa8eeb8643179392ec66f | f1983cf2b43de444b2221286507793472358d2df039c23287f0e19e3dc348d87 |
| GHSA record `ghsa_rec/CVE-2026-114140.json` (GHSA-pjvx-prjx-h659) | https://github.com/advisories/GHSA-pjvx-prjx-h659 | — | 95663537c6ef309fc1ee2f84b1f5563a9ee26b661e52c18e1e1fddbdf646eed7 |
| NVD record `nvd/CVE-2026-114140.json` (Awaiting Analysis, published 2026-10-21) | https://nvd.nist.gov/vuln/detail/CVE-2026-114140 | — | 6c229173356c54cfdbdb867e000dc405062a03d7d3f79c2787f441b5c4cb856c |

Used for: affected range >= 5.4.0, <= 7.17.1, fixed in 7.17.2 (GHSA); CWE-22;
the PoC filename `../../../tmp/PWNED.png` (GHSA); the code change (diff lines
8-27) and the new tests (diff lines 46-65).

No source contained instructions addressed to a tool or agent.

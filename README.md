# cortex9-nbconvert-output-filename-traversal-model

Path-resolution model of **CVE-2026-114140** (GHSA-pjvx-prjx-h659), the
path traversal in nbconvert's `ExtractOutputPreprocessor`
(`nbconvert/preprocessors/extractoutput.py`): the output filename taken from
a notebook's `out.metadata["filename"]` was used as is, so `../../x` or
`/abs/x` could place an extracted output outside the output directory. Fixed
in nbconvert 7.17.2 by commit ce4bd99aec31 (`pre` = before, `post` = after).

Educational, offline, deterministic, Python stdlib only. nbconvert is not
installed or run, no notebook is converted, and the only files written are
inside a `tempfile` sandbox during one test.

Spanish: [README.es.md](README.es.md). Exercises: [PRACTICE.md](PRACTICE.md).

## What the fix changes (lines of the saved diff)

| Diff lines | pre | post |
|---|---|---|
| 8 (context) | empty or missing `filename` → default name | same |
| 9 (removed) | `filename = out.metadata["filename"]`, unchanged | — |
| 10-12 (added) | — | `filename = os.path.basename(fname)` |
| 13-18 (added) | — | empty basename → warning and `continue` (skip) |
| 19-25 (added) | — | warning when components were stripped |
| 26-27 (context) | append `ext` if missing | same |
| 48-56, 58-65 (tests) | — | `/tmp/evil.png`, `../../evil.png`, `sub/evil.png` → `nb_files/evil.png`; `../../../tmp/` skipped |

The join of `output_files_dir` and the filename follows the advisory text and
the new test (diff line 54). Placing that under the build directory
(`/sandbox/build`, a symbolic string) is a **model assumption**.

## Differential evidence (`results/differential.csv`)

| Case | pre | post |
|---|---|---|
| `../../evil.txt` | `ESCAPE_ROOT` → `/sandbox/evil.txt.png` | `INSIDE` → `nb_files/evil.txt.png` |
| `/abs/x` | `ESCAPE_ROOT` → `/abs/x.png` | `INSIDE` → `nb_files/x.png` |
| `a/../../x` | `ESCAPE_FILES_DIR` → `/sandbox/build/x.png` | `INSIDE` |
| `../../../tmp/PWNED.png` (GHSA PoC name) | `ESCAPE_ROOT` → `/tmp/PWNED.png` | `INSIDE`, warning |
| `../../../tmp/` (diff line 61) | `ESCAPE_ROOT` → `/tmp/.png` | `SKIP` |
| `img.png` (negative) | `INSIDE` | `INSIDE` |

All 9 positives escape `pre` and are `INSIDE` or `SKIP` `post`; all 5
negatives keep their label. On a corpus of 9,360 generated names
`post` never escapes the build directory, and with a real extension
(`.png`) never leaves `output_files_dir`.

**Model edge, unverified:** with the name `..` and `ext == "."` (what diff
line 7 would give for a MIME type ending in `/`), `post` keeps `..` and the
target is the build directory itself (`a02`). It stays inside the build
directory, it was not checked whether nbconvert can ever produce that
`ext`, and it is not a finding.

## Run

```sh
python3 tests/run.py                                   # any skip = failure
python3 scripts/derive_expected.py | diff - fixtures/expected.tsv
PYTHONPATH=src python3 -m nbconvert_model results fixtures/cases.tsv /tmp/r && diff -r results /tmp/r
PYTHONPATH=src python3 -m nbconvert_model case pre '../../evil.txt'
```

`fixtures/cases.tsv` holds hand-derived labels; `scripts/derive_expected.py`
re-implements basename, join and POSIX normalisation without `os.path` or
the model and writes `fixtures/expected.tsv`; the tests compare all three.

See [LIMITATIONS.md](LIMITATIONS.md) and [SOURCES.md](SOURCES.md).
License: Apache-2.0.

"""CLI.

  python -m nbconvert_model case <pre|post> <metadata-filename> [ext] [files_dir]
  python -m nbconvert_model results <cases.tsv> <outdir>
"""
import csv
import hashlib
import io
import sys
from pathlib import Path

from .model import MISSING, VERSIONS, run_case
from .fixtures import load_cases

# Lines of CVE-2026-114140_nbconvert_ce4bd99aec31.diff that decide each branch.
RULES = {
    ("pre", "DEFAULT"): "8", ("post", "DEFAULT"): "8",
    ("pre", "METADATA"): "8-9;26-27", ("post", "METADATA"): "10-12;19-27",
    ("post", "SKIP"): "10-18",
}

FIELDS = ["id", "kind", "version", "branch", "name", "warn", "target",
          "inside_root", "inside_files_dir", "label"]


def _rows(cases):
    for c in cases:
        for v in VERSIONS:
            o = run_case(v, c["meta"], c["ext"], c["files_dir"])
            yield [c["id"], c["kind"], v, o.branch, o.name, o.warn, o.target,
                   o.inside_root, o.inside_files_dir, o.label]


def _csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode()


def results(cases_path, outdir):
    cases = load_cases(cases_path)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(_rows(cases))
    files = {"cases.csv": _csv(FIELDS, rows)}
    # Differential view: one row per case, pre vs post side by side.
    diff_rows = []
    by_id = {}
    for r in rows:
        by_id.setdefault(r[0], {})[r[2]] = r
    for cid, d in by_id.items():
        pre, post = d["pre"], d["post"]
        diff_rows.append([cid, pre[1], pre[9], post[9], pre[6], post[6],
                          int(pre[9] != post[9]), RULES[("pre", pre[3])],
                          RULES[("post", post[3])]])
    files["differential.csv"] = _csv(
        ["id", "kind", "pre_label", "post_label", "pre_target", "post_target",
         "changed", "pre_diff_lines", "post_diff_lines"],
        diff_rows)
    sums = []
    for name in sorted(files):
        (out / name).write_bytes(files[name])
        sums.append(f"{hashlib.sha256(files[name]).hexdigest()}  {name}\n")
    (out / "SHA256SUMS").write_text("".join(sums))


def main(argv):
    if len(argv) >= 2 and argv[0] == "case" and argv[1] in VERSIONS:
        meta = argv[2] if len(argv) > 2 else MISSING
        ext = argv[3] if len(argv) > 3 else ".png"
        fdir = argv[4] if len(argv) > 4 else "nb_files"
        o = run_case(argv[1], meta, ext, fdir)
        print(",".join(str(x) for x in (o.version, o.branch, o.name, o.warn,
                                         o.target, o.label)))
        return 0
    if len(argv) == 3 and argv[0] == "results":
        results(argv[1], argv[2])
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

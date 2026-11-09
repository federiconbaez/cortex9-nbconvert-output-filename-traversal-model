#!/usr/bin/env python3
"""Independent derivation of fixtures/expected.tsv.

Written from the saved diff (CVE-2026-114140_nbconvert_ce4bd99aec31.diff,
lines 8-27) and the POSIX path rules, NOT from src/. It does not import the
model, os.path or posixpath: basename, join and normalisation are
re-implemented here on plain strings so that a bug in one implementation
shows up as a mismatch with the other.
"""
import sys
from pathlib import Path

ROOT = "/sandbox/build"
HERE = Path(__file__).resolve().parent.parent


def base_name(p):
    # POSIX basename: everything after the last "/".
    i = p.rfind("/")
    return p if i < 0 else p[i + 1:]


def join2(a, b):
    # POSIX join: an absolute b discards a.
    if b.startswith("/"):
        return b
    if a == "" or a.endswith("/"):
        return a + b
    return a + "/" + b


def normalise(p):
    # POSIX normpath: exactly two leading slashes are kept, one or 3+ become one.
    if p.startswith("//") and not p.startswith("///"):
        lead = "//"
    elif p.startswith("/"):
        lead = "/"
    else:
        lead = ""
    stack = []
    for seg in p.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if stack and stack[-1] != "..":
                stack.pop()
            elif not lead:
                stack.append("..")
            continue
        stack.append(seg)
    out = lead + "/".join(stack)
    return out or "."


def under(path, base):
    return path == base or path.startswith(base + "/")


def derive(version, meta, ext, fdir):
    # diff line 8: `if out.metadata.get("filename", ""):`
    if meta is None or meta == "":
        return ["DEFAULT", "", 0, "", 0, 0, "DEFAULT"]
    warn = 0
    if version == "pre":
        name = meta                                   # diff line 9
    else:
        name = base_name(meta)                        # diff line 12
        if name == "":
            return ["SKIP", "", 0, "", 0, 0, "SKIP"]  # diff lines 13-18
        warn = int(name != meta)                      # diff lines 19-25
    if not name.endswith(ext):                        # diff lines 26-27
        name = name + ext
    target = normalise(join2(ROOT, join2(fdir, name)))
    files_dir = normalise(join2(ROOT, fdir))
    in_root = int(under(target, ROOT))
    in_fdir = int(under(target, files_dir) and target != files_dir)
    label = "INSIDE" if in_fdir else ("ESCAPE_FILES_DIR" if in_root else "ESCAPE_ROOT")
    return ["METADATA", name, warn, target, in_root, in_fdir, label]


def read_cases(path):
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        cid, kind, meta, ext, fdir, hp, hq = line.split("\t")
        meta = {"@missing": None, "@empty": ""}.get(meta, meta)
        yield cid, kind, meta, ext, fdir, hp, hq


def main():
    cases = sys.argv[1] if len(sys.argv) > 1 else HERE / "fixtures" / "cases.tsv"
    out = ["\t".join(["id", "version", "branch", "name", "warn", "target",
                      "inside_root", "inside_files_dir", "label"])]
    for cid, kind, meta, ext, fdir, hp, hq in read_cases(cases):
        for version, hand in (("pre", hp), ("post", hq)):
            row = derive(version, meta, ext, fdir)
            if row[-1] != hand:
                sys.exit(f"{cid}/{version}: derived {row[-1]} != hand label {hand}")
            out.append("\t".join([cid, version] + [str(x) for x in row]))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

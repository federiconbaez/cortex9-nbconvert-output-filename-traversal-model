"""Path-resolution model of the output-filename handling in nbconvert's
ExtractOutputPreprocessor before and after commit ce4bd99aec31.

Diff lines cited refer to
sources/cve2026/diffs/CVE-2026-114140_nbconvert_ce4bd99aec31.diff
(sha256 f1983cf2b43de444b2221286507793472358d2df039c23287f0e19e3dc348d87).

Nothing here imports or runs nbconvert. Paths are POSIX strings handled with
posixpath only; Windows separators are NOT modelled (see LIMITATIONS.md).
"""
from __future__ import annotations

import posixpath
from dataclasses import dataclass

VERSIONS = ("pre", "post")

# Symbolic build directory. It is a string, never a real directory.
ROOT = "/sandbox/build"

MISSING = object()  # metadata has no "filename" key


@dataclass(frozen=True)
class Outcome:
    version: str
    branch: str          # METADATA | DEFAULT | SKIP
    name: str            # filename after the preprocessor ('' if none)
    warn: int            # post only: 1 if the warning at diff 19-25 fires
    target: str          # normalised absolute target ('' if none)
    inside_root: int
    inside_files_dir: int
    label: str           # INSIDE | ESCAPE_FILES_DIR | ESCAPE_ROOT | SKIP | DEFAULT


def extract_name(version: str, meta, ext: str):
    """Return (branch, name, warn).

    pre  (diff line 8 context, line 9 removed, lines 26-27 context):
         if out.metadata.get("filename", ""):
             filename = out.metadata["filename"]
             if not filename.endswith(ext): filename += ext
    post (diff lines 10-27): basename, skip on empty basename (13-18),
         warn when the basename differs (19-25), then the same ext rule.
    """
    if version not in VERSIONS:
        raise ValueError(f"unknown version {version!r}")
    if not isinstance(ext, str):
        raise TypeError("ext must be a string")
    if meta is MISSING or not meta:        # diff line 8: .get("filename", "")
        return "DEFAULT", "", 0
    if not isinstance(meta, str):
        raise TypeError("metadata filename must be a string")
    warn = 0
    if version == "pre":
        filename = meta                    # diff line 9 (removed)
    else:
        fname = meta                       # diff line 10
        filename = posixpath.basename(fname)   # diff line 12 (os.path on POSIX)
        if not filename:                   # diff lines 13-18
            return "SKIP", "", 0
        if filename != fname:              # diff lines 19-25
            warn = 1
    if not filename.endswith(ext):         # diff lines 26-27 (context)
        filename += ext
    return "METADATA", filename, warn


def _inside(path: str, base: str) -> bool:
    return path == base or path.startswith(base.rstrip("/") + "/")


def resolve(files_dir: str, name: str, root: str = ROOT):
    """Where the writer would put the file.

    Modelled as os.path.join(root, os.path.join(files_dir, name)), then
    normalised. The join of output_files_dir and the filename is what the
    advisory describes ("joins ... to output_files_dir") and what the new test
    expects (diff line 54: os.path.join("nb_files", "evil.png")). Joining the
    result under the build directory is a MODEL ASSUMPTION, not in the diff.
    """
    rel = posixpath.join(files_dir, name)
    target = posixpath.normpath(posixpath.join(root, rel))
    fdir = posixpath.normpath(posixpath.join(root, files_dir))
    return target, int(_inside(target, root)), int(_inside(target, fdir) and target != fdir)


def run_case(version: str, meta, ext: str, files_dir: str, root: str = ROOT) -> Outcome:
    branch, name, warn = extract_name(version, meta, ext)
    if branch != "METADATA":
        return Outcome(version, branch, "", 0, "", 0, 0, branch)
    target, in_root, in_fdir = resolve(files_dir, name, root)
    if in_fdir:
        label = "INSIDE"
    elif in_root:
        label = "ESCAPE_FILES_DIR"
    else:
        label = "ESCAPE_ROOT"
    return Outcome(version, branch, name, warn, target, in_root, in_fdir, label)

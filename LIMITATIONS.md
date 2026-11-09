# Limitations

- **A model is not a finding.** This repo re-states public behaviour from
  CVE-2026-114140, its advisory and the fix commit. Nothing here is a new
  vulnerability, and nothing was reproduced against a real nbconvert build.
- **Strings only.** The model computes where a file *would* be written.
  nbconvert is not imported; templates, exporters, `FilesWriter` and the
  default naming branch (`output_{cell}_{index}`) are not modelled. The
  default branch is only labelled `DEFAULT`.
- **Writer join is an assumption.** The diff shows the filename and the
  test's `os.path.join("nb_files", "evil.png")` (line 54). Joining that under
  the build directory follows the advisory text, not code in the diff.
- **POSIX only.** `posixpath` is used everywhere. Behaviour on Windows
  (backslash `\` separators, drive letters, `ntpath.basename`) was **not
  verified**; on POSIX `..\..\evil` is a single file name (case `a01`).
- **`ext`.** Taken from the fixture. How nbconvert derives it (only the
  fallback at diff line 7 is visible) is not modelled. The `ext == "."` edge
  (`a02`) is an unverified model observation.
- **Symlinks, case-insensitive filesystems, NUL bytes, encodings** and
  pre-existing files are not modelled. The sandbox test creates no symlinks.
- **Versions.** Only the code before and after ce4bd99aec31 is modelled; the
  affected range (>= 5.4.0, <= 7.17.1) is taken from the advisory, not tested.
- **Corpus** in the tests is a fixed generated grid, not a proof.

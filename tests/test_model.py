import importlib.util
import itertools
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from nbconvert_model import run_case
from nbconvert_model.fixtures import load_cases
from nbconvert_model.model import MISSING, ROOT, extract_name

REPO = Path(__file__).resolve().parent.parent
CASES = load_cases(REPO / "fixtures" / "cases.tsv")


def _load_derive():
    spec = importlib.util.spec_from_file_location("derive", REPO / "scripts" / "derive_expected.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DERIVE = _load_derive()


def _expected():
    rows = {}
    lines = (REPO / "fixtures" / "expected.tsv").read_text(encoding="utf-8").splitlines()
    for line in lines[1:]:
        f = line.split("\t")
        rows[(f[0], f[1])] = f[2:]
    return rows


def _row(o):
    return [o.branch, o.name, str(o.warn), o.target, str(o.inside_root),
            str(o.inside_files_dir), o.label]


class Fixtures(unittest.TestCase):
    def test_fixture_count(self):
        kinds = [c["kind"] for c in CASES]
        self.assertGreaterEqual(kinds.count("pos"), 9)
        self.assertGreaterEqual(kinds.count("neg"), 5)
        self.assertGreaterEqual(kinds.count("adv"), 10)
        self.assertEqual(len({c["id"] for c in CASES}), len(CASES))

    def test_model_matches_independent_expected(self):
        exp = _expected()
        self.assertEqual(len(exp), 2 * len(CASES))
        for c in CASES:
            for v in ("pre", "post"):
                with self.subTest(case=c["id"], version=v):
                    o = run_case(v, c["meta"], c["ext"], c["files_dir"])
                    self.assertEqual(_row(o), exp[(c["id"], v)])

    def test_model_matches_hand_labels(self):
        for c in CASES:
            with self.subTest(case=c["id"]):
                self.assertEqual(run_case("pre", c["meta"], c["ext"], c["files_dir"]).label, c["hand_pre"])
                self.assertEqual(run_case("post", c["meta"], c["ext"], c["files_dir"]).label, c["hand_post"])

    def test_expected_tsv_is_what_derive_produces(self):
        out = subprocess.run([sys.executable, str(REPO / "scripts" / "derive_expected.py")],
                             check=True, capture_output=True, text=True, encoding="utf-8").stdout
        self.assertEqual(out, (REPO / "fixtures" / "expected.tsv").read_text(encoding="utf-8"))


class Differential(unittest.TestCase):
    def test_every_positive_escapes_pre_and_is_contained_post(self):
        for c in CASES:
            if c["kind"] != "pos":
                continue
            with self.subTest(case=c["id"]):
                pre = run_case("pre", c["meta"], c["ext"], c["files_dir"])
                post = run_case("post", c["meta"], c["ext"], c["files_dir"])
                self.assertIn(pre.label, ("ESCAPE_ROOT", "ESCAPE_FILES_DIR"))
                self.assertIn(post.label, ("INSIDE", "SKIP"))

    def test_negatives_keep_their_label(self):
        for c in CASES:
            if c["kind"] != "neg":
                continue
            with self.subTest(case=c["id"]):
                pre = run_case("pre", c["meta"], c["ext"], c["files_dir"])
                post = run_case("post", c["meta"], c["ext"], c["files_dir"])
                self.assertEqual(pre.label, post.label)

    def test_diff_test_vectors(self):
        # diff lines 48-56: all three names end as nb_files/evil.png post-fix.
        for name in ["/tmp/evil.png", "../../evil.png", "sub/evil.png"]:
            o = run_case("post", name, ".png", "nb_files")
            self.assertEqual(o.name, "evil.png")
            self.assertEqual(o.target, ROOT + "/nb_files/evil.png")
        # diff lines 58-65: empty basename is skipped.
        self.assertEqual(run_case("post", "../../../tmp/", ".png", "nb_files").label, "SKIP")

    def test_warning_only_when_components_stripped(self):
        # diff lines 19-25
        self.assertEqual(extract_name("post", "img.png", ".png"), ("METADATA", "img.png", 0))
        self.assertEqual(extract_name("post", "a/img.png", ".png"), ("METADATA", "img.png", 1))
        self.assertEqual(extract_name("pre", "a/img.png", ".png")[2], 0)


class Adversarial(unittest.TestCase):
    SEGMENTS = ["..", ".", "a", "", "\\", "\u2025", "x.png", "..."]

    def _corpus(self):
        for n in range(1, 5):
            for combo in itertools.product(self.SEGMENTS, repeat=n):
                yield "/".join(combo)
                yield "/" + "/".join(combo)

    def test_post_never_leaves_files_dir_with_real_extension(self):
        count = 0
        for name in self._corpus():
            o = run_case("post", name, ".png", "nb_files")
            count += 1
            self.assertIn(o.label, ("INSIDE", "SKIP", "DEFAULT"), name)
        self.assertGreater(count, 9000)

    def test_post_never_leaves_root_for_any_ext(self):
        for name in self._corpus():
            for ext in (".png", ".", ".txt", ""):
                o = run_case("post", name, ext, "nb_files")
                self.assertNotEqual(o.label, "ESCAPE_ROOT", (name, ext))

    def test_model_and_derivation_agree_on_corpus(self):
        for name in self._corpus():
            for v in ("pre", "post"):
                for ext in (".png", "."):
                    o = run_case(v, name, ext, "nb_files")
                    d = DERIVE.derive(v, name, ext, "nb_files")
                    self.assertEqual(_row(o), [str(x) for x in d], (v, name, ext))

    def test_pre_escapes_exist_in_corpus(self):
        labels = {run_case("pre", n, ".png", "nb_files").label for n in self._corpus()}
        self.assertTrue({"ESCAPE_ROOT", "ESCAPE_FILES_DIR", "INSIDE"} <= labels)

    def test_bad_inputs_rejected(self):
        with self.assertRaises(ValueError):
            run_case("master", "x", ".png", "nb_files")
        with self.assertRaises(TypeError):
            run_case("post", 7, ".png", "nb_files")
        with self.assertRaises(TypeError):
            run_case("post", "x", None, "nb_files")

    def test_missing_and_empty_are_default(self):
        for v in ("pre", "post"):
            self.assertEqual(run_case(v, MISSING, ".png", "nb_files").label, "DEFAULT")
            self.assertEqual(run_case(v, "", ".png", "nb_files").label, "DEFAULT")

    def test_backslash_is_not_a_separator_in_this_model(self):
        # POSIX only. Windows (ntpath) is not modelled: see LIMITATIONS.md.
        o = run_case("post", "..\\..\\evil", ".png", "nb_files")
        self.assertEqual(o.name, "..\\..\\evil.png")
        self.assertEqual(o.warn, 0)


class Sandbox(unittest.TestCase):
    """Writes inside a temporary directory only, to check that the predicted
    target is where the filesystem really puts the file (no nbconvert)."""

    def test_writes_land_where_the_model_says(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = os.path.realpath(tmp)
            root = os.path.join(tmp, "j", "k", "build")
            os.makedirs(os.path.join(root, "nb_files"))
            written = 0
            for c in CASES:
                for v in ("pre", "post"):
                    o = run_case(v, c["meta"], c["ext"], c["files_dir"], root=root)
                    if o.label in ("DEFAULT", "SKIP"):
                        continue
                    with self.subTest(case=c["id"], version=v):
                        if not o.target.startswith(tmp + "/"):
                            self.assertEqual(o.inside_root, 0)
                            continue          # never write outside the sandbox
                        if os.path.isdir(o.target):
                            self.assertEqual(o.inside_files_dir, 0)
                            continue
                        rel = os.path.join(c["files_dir"], o.name)
                        dest = os.path.join(root, rel)   # what a writer would open
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        with open(dest, "wb") as fh:
                            fh.write(b"g")
                        real = os.path.realpath(dest)
                        self.assertEqual(real, o.target)
                        rp = Path(real)
                        self.assertEqual(int(rp.is_relative_to(root)), o.inside_root)
                        written += 1
            self.assertGreaterEqual(written, 30)


class Practice(unittest.TestCase):
    """Answers to PRACTICE.md (practice_level_N)."""

    def test_practice_level_1(self):
        self.assertEqual(run_case("pre", "img.png", ".png", "nb_files").target, ROOT + "/nb_files/img.png")

    def test_practice_level_2(self):
        self.assertEqual(run_case("pre", "../../evil.txt", ".png", "nb_files").target, "/sandbox/evil.txt.png")

    def test_practice_level_3(self):
        self.assertEqual(run_case("pre", "/abs/x", ".png", "nb_files").target, "/abs/x.png")

    def test_practice_level_4(self):
        o = run_case("post", "../../../tmp/PWNED.png", ".png", "nb_files")
        self.assertEqual((o.name, o.warn, o.label), ("PWNED.png", 1, "INSIDE"))

    def test_practice_level_5(self):
        self.assertEqual(run_case("post", "../../../tmp/", ".png", "nb_files").label, "SKIP")

    def test_practice_level_6(self):
        o = run_case("post", "..", ".", "nb_files")
        self.assertEqual((o.target, o.label), (ROOT, "ESCAPE_FILES_DIR"))

    def test_practice_level_7(self):
        self.assertEqual(run_case("post", "..\\..\\evil", ".png", "nb_files").label, "INSIDE")


class Results(unittest.TestCase):
    def test_results_regenerate_byte_identical(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            env = dict(os.environ, PYTHONPATH=str(REPO / "src"))
            for d in (a, b):
                subprocess.run([sys.executable, "-m", "nbconvert_model", "results",
                                str(REPO / "fixtures" / "cases.tsv"), d], check=True, env=env)
            for name in ("cases.csv", "differential.csv", "SHA256SUMS"):
                ba = Path(a, name).read_bytes()
                self.assertEqual(ba, Path(b, name).read_bytes())
                self.assertEqual(ba, (REPO / "results" / name).read_bytes(), name)


if __name__ == "__main__":
    unittest.main()

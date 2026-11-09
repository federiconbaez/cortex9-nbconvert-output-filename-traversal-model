"""Reader for fixtures/cases.tsv. Tokens: @missing (no key), @empty ('')."""
from .model import MISSING

TOKENS = {"@missing": MISSING, "@empty": ""}


def load_cases(path):
    cases = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) != 7:
                raise ValueError(f"bad fixture line: {line!r}")
            cid, kind, meta, ext, fdir, hand_pre, hand_post = f
            cases.append(dict(id=cid, kind=kind, meta=TOKENS.get(meta, meta),
                              ext=ext, files_dir=fdir,
                              hand_pre=hand_pre, hand_post=hand_post))
    return cases

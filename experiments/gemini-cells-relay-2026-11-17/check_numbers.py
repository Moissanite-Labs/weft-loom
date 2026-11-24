#!/usr/bin/env python3
"""Check that every decimal figure in the README and in the note traces to an output file.

    python3 check_numbers.py

A figure with d decimals passes if some number in the source files equals it when rounded to
d decimals. A plain substring match would let 0.07 pass against 0.075, so numbers are
compared as numbers. Whole numbers are not checked. A figure that is derived by hand, or
that restates a setting, is listed in ALLOWED with where it comes from. Exit status 1 if
any figure is left unexplained.
"""

import re
import sys
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NUM = re.compile(r"(?<![\w.])[-+]?\d+\.\d+(?![\w]|\.\d)")

SOURCES = [HERE / "results" / n for n in ("tables.md", "explore.md", "summary.json", "seed_exam.json", "ref_exam.json",
                                           "gate_noise.json", "calibration.jsonl", "kexam-1.jsonl", "forgery_check.out",
                                           "changes/summary.md")]
SOURCES += [HERE / "PREREG.md", HERE / "second_count" / "recount_final.out", HERE / "second_count" / "recount.out",
            HERE / "referee" / "tasks" / "selftest.out"]
SOURCES += sorted((HERE / "results" / "faulted").glob("*/*.jsonl"))
BLOCK2 = sorted((HERE / "block2").glob("*.out")) + [HERE / "block2" / "analyze_a_dryrun.md"]
GAME = [REPO / "notes" / "prototypes" / "gemini-cells-game" / n for n in ("game.out", "README.md", "recheck.out")]

ALLOWED = {   # figure: where it comes from
    "README.md": {
        "22.20": "the ledger file of the run root, read when the record was packed",
        "1.47": "the ledger file of the one-call exam, read when the record was packed",
        "6.18": "the kernel version of the machine", "3.13": "the Python version", "2.1": "the version of the command line tool",
        "0.743": "results/faulted/twin-stack-collective-r2/exam_resit.jsonl, mean over all 36 exam tasks",
        "0.667": "results/faulted/twin-stack-collective-r2/log.jsonl, turn 3, old harness",
        "0.652": "results/faulted/twin-stack-collective-r2/log.jsonl, turn 3, candidate",
    },
    "gemini-cells.md": {
        "0.064": "tables.md, contrast live builder minus seed builder", "4.1": "size of the seed harness in kilobytes (4,115 bytes)",
        "5.1": "tables.md, mean bytes of a final harness, lowest arm", "6.8": "tables.md, mean bytes of a final harness, highest arm",
        "0.45": "tables.md, pooled gain over the seed, rounded", "0.9": "a round figure for the level of the reference harness",
    },
}


def numbers(text: str) -> list[Decimal]:
    return [Decimal(m.group().lstrip("+")) for m in NUM.finditer(text)]


def check(doc: Path, sources: list[Path], sections: tuple[str, ...] | None, text: str | None = None) -> list[str]:
    """Untraced figures of doc (or of `text`, read as if it were doc)."""
    text = doc.read_text() if text is None else text
    if sections:
        parts = re.split(r"^## ", text, flags=re.M)
        text = "\n".join(p for p in parts if p.split("\n", 1)[0].strip() in sections)
    pool = set()
    for f in sources:
        pool.update(abs(x) for x in numbers(f.read_text(errors="replace")))
    allowed = ALLOWED.get(doc.name, {})
    bad = []
    for m in NUM.finditer(text):
        tok = m.group().lstrip("+-")
        if tok in allowed:
            continue
        d = Decimal(tok)
        q = Decimal(1).scaleb(d.as_tuple().exponent)
        if any(x == d or (x.as_tuple().exponent <= d.as_tuple().exponent
                          and (x.quantize(q, ROUND_HALF_EVEN) == d or x.quantize(q, ROUND_HALF_UP) == d))
               for x in pool):
            continue
        line = text[:m.start()].count("\n")
        bad.append(f"{doc.name}: {m.group()} (near: {text.splitlines()[line][:90]!r})")
    return bad


# (document, sources, sections or None for all). The plan is checked against a narrow pool:
# the block 2 outputs and the record's summary tables. A wide pool holds so many numbers that
# a wrong figure with three decimals often finds a match by chance (a planted 0.087 for 0.081
# did). block2/check_numbers_power.py measures how often that happens for each document.
CHECKS = [
    (HERE / "README.md", SOURCES + BLOCK2, None),
    (HERE / "block2" / "PLAN.md", BLOCK2 + [HERE / "results" / "explore.md", HERE / "results" / "tables.md"], None),
    (REPO / "notes" / "gemini-cells.md", SOURCES + GAME + BLOCK2 + [HERE / "README.md"],
     ("What a scoring rule pays for: an exact model", "What live cells did: a pilot", "The reply, claim by claim",
      "Transposition", "What would decide it")),
]


def main() -> int:
    bad = []
    for doc, sources, sections in CHECKS:
        bad += check(doc, sources, sections)
    for b in bad:
        print("UNTRACED", b)
    print(f"{len(bad)} figures without a source")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

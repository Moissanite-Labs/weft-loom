"""Checks that every line of results.jsonl names a seed inside the pilot
evaluation ranges (tier S 310000 to 310049, tier M 360000 to 360049) and a
tier that matches its seed, and that n and passed in every cell of summary.json
agree with the lines.

    python3 -I -B check_seeds.py [PATH_TO_results.jsonl]

Prints one summary line and exits 0 if every line passes, 1 otherwise.
Standard library only.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = {"S": (310000, 310049), "M": (360000, 360049)}


def main(argv):
    path = argv[1] if len(argv) > 1 else os.path.join(HERE, "results.jsonl")
    bad, n, seen = [], 0, set()
    with open(path, "r", encoding="utf-8") as fh:
        for ln, raw in enumerate(fh, 1):
            if not raw.strip():
                continue
            n += 1
            try:
                row = json.loads(raw)
            except ValueError:
                bad.append((ln, "not JSON"))
                continue
            tier, seed = row.get("tier"), row.get("seed")
            ok = (tier in PILOT and isinstance(seed, int) and not isinstance(seed, bool)
                  and PILOT[tier][0] <= seed <= PILOT[tier][1])
            if not ok:
                bad.append((ln, "tier %r seed %r" % (tier, seed)))
            seen.add((tier, seed))
    # summary.json must agree with the lines on n and passed in every cell
    summ = os.path.join(os.path.dirname(os.path.abspath(path)), "summary.json")
    if os.path.exists(summ):
        with open(summ, "r", encoding="utf-8") as fh:
            S = json.load(fh)
        with open(path, "r", encoding="utf-8") as fh:
            rows = [json.loads(raw) for raw in fh if raw.strip()]
        for mode in ("F", "R"):
            for cell, e in sorted(S[mode].items()):
                text, tier = cell.split("_")
                rs = [r for r in rows if r["mode"] == mode and r["text"] == text and r["tier"] == tier]
                got = (len(rs), sum(r["outcome"] == "passed" for r in rs))
                if got != (e["n"], e["passed"]):
                    bad.append((0, "summary.json cell %s %s says %s, the lines give %s" % (mode, cell, (e["n"], e["passed"]), got)))
    for ln, why in bad:
        print("line %d: outside the pilot evaluation ranges: %s" % (ln, why))
    print("%d lines, %d distinct (tier, seed) pairs, %d outside the pilot evaluation ranges" % (n, len(seen), len(bad)))
    return 1 if bad or n == 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

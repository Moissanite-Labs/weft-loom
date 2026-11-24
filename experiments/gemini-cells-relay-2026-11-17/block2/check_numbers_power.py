#!/usr/bin/env python3
"""How often check_numbers.py catches a wrong figure. For each checked document, plant one
error at a time in a random decimal figure (its last digit moved by 1 to 3 units, either
way) and count how often the check reports it. Nothing on disk is changed.

    python3 -I -B block2/check_numbers_power.py > block2/check_numbers_power.out
"""
import random
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import check_numbers as cn  # noqa: E402

PLANTS = 60
SEED = 20261124


def main():
    print(f"{PLANTS} plants per document, seed {SEED}. A plant moves the last digit of one figure by 1 to 3"
          " units up or down.\n")
    print(f"{'document':28} {'figures':>8} {'caught':>7} {'rate':>6}")
    for doc, sources, sections in cn.CHECKS:
        rng = random.Random(f"{SEED}|{doc.name}")   # per document, so one document's edits leave the others' draws alone
        text = doc.read_text()
        if cn.check(doc, sources, sections, text):
            print(f"{doc.name:28} not clean before planting; skipped")
            continue
        if sections:
            parts = re.split(r"^## ", text, flags=re.M)
            keep = [p for p in parts if p.split("\n", 1)[0].strip() in sections]
            scope_spans = [(text.index(p), text.index(p) + len(p)) for p in keep]
        else:
            scope_spans = [(0, len(text))]
        allowed = cn.ALLOWED.get(doc.name, {})
        figures = [m for m in cn.NUM.finditer(text)
                   if any(a <= m.start() < b for a, b in scope_spans) and m.group().lstrip("+-") not in allowed]
        caught = 0
        for _ in range(PLANTS):
            m = rng.choice(figures)
            tok = m.group()
            d = Decimal(tok.lstrip("+-"))
            unit = Decimal(1).scaleb(d.as_tuple().exponent)
            step = rng.choice([1, 2, 3]) * rng.choice([-1, 1])
            wrong = d + step * unit
            if wrong < 0:
                wrong = d - step * unit
            planted = text[:m.start()] + tok.replace(str(d), str(wrong)) + text[m.end():]
            caught += bool(cn.check(doc, sources, sections, planted))
        print(f"{doc.name:28} {len(figures):8d} {caught:7d} {caught / PLANTS:6.2f}")


if __name__ == "__main__":
    main()

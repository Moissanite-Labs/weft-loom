"""Advocate pass: test the playbook's "~30%-45% of MLP neurons" in four symbol kinds (N10)
and look for any site figure that gives "7.8%-17.2%", from the saved index page (read only).

Bar widths are the page's own 4-decimal flex values. Stdlib only; no bare assert.
"""
import html
import re
import sys

FOUR = (
    "Punctuation, LaTeX marks and word pieces",
    "Digits, hex escapes and character names",
    "Single letters and capitals",
    "Name and place-name pieces",
)


DOM5 = []


def main(path):
    with open(path, encoding="utf-8") as fh:
        t = fh.read()
    cards = re.findall(r'<h3>(.*?)</h3>(.*?)</div>', t, flags=re.S)
    rows = []
    for name, body in cards:
        bars = re.findall(r'flex:([0-9.]+)[;"][^>]*?title="([^"]+?): (\d+)% of neurons"', body)
        if not bars:
            continue
        d = {html.unescape(k): float(f) for f, k, _p in bars}
        rows.append((html.unescape(name), d))
    print("cards with kind bars:", len(rows))
    s4 = []
    for name, d in rows:
        four = sum(d.get(k, 0.0) for k in FOUR)
        dom5 = four + d.get("Everyday nouns, adverbs and adjectives", 0.0)
        DOM5.append(dom5)
        dark = d.get("In no shared family", 0.0)
        s4.append((four, name, dark))
    s4.sort()
    for four, name, dark in s4:
        print("%-40s four-kind share %.4f   no-family bar %.4f" % (name, four, dark))
    vals = [x[0] for x in s4]
    print("four symbol kinds: min %.4f max %.4f; models inside [0.30, 0.45]: %d of %d" % (
        min(vals), max(vals), sum(1 for v in vals if 0.30 <= v <= 0.45), len(vals)))
    print("whole Symbols domain (5 kinds): min %.4f max %.4f; inside [0.30, 0.45]: %d of %d" % (
        min(DOM5), max(DOM5), sum(1 for v in DOM5 if 0.30 <= v <= 0.45), len(DOM5)))
    darks = sorted(x[2] for x in s4)
    print("no-family bar: min %.4f max %.4f" % (darks[0], darks[-1]))
    hits = [x for x in s4 if abs(x[2] - 0.078) < 0.0006 or abs(x[2] - 0.172) < 0.0006]
    print("no-family bars at 7.8% or 17.2% (+-0.06 pt):", [(n, d) for _f, n, d in hits])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

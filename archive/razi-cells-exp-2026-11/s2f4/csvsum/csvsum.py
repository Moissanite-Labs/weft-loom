import sys


def main():
    buf = sys.stdin.buffer.read().strip()
    toks = buf.replace(b"\n", b",").split(b",")
    # toks[0:3] is header; then triples (id, cat, val)
    cats = toks[4::3]
    vals = toks[5::3]
    sums = {}
    get = sums.get
    for cat, v in zip(cats, map(float, vals)):
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + ("%.2f" % sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

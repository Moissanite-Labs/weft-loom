import sys


def main():
    t = sys.stdin.buffer.read().replace(b"\n", b",").split(b",")
    cats = t[4::3]
    vals = list(map(float, t[5::3]))
    sums = {}
    get = sums.get
    for cat, v in zip(cats, vals):
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append("%s,%.2f" % (cat.decode(), sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

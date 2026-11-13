import sys


def main():
    data = sys.stdin.buffer.read()
    toks = data.replace(b",", b" ").split()
    cats = toks[4::3]
    vals = list(map(float, toks[5::3]))
    sums = {}
    get = sums.get
    for cat, v in zip(cats, vals):
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + "," + ("%.2f" % sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


if __name__ == "__main__":
    main()

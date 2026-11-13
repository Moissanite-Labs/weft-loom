import sys

def main():
    t = sys.stdin.buffer.read().replace(b",", b"\n").split()
    cats = t[4::3]
    vals = t[5::3]
    sums = {}
    get = sums.get
    for c, v in zip(cats, map(float, vals)):
        sums[c] = get(c, 0.0) + v
    out = [c.decode() + "," + ("%.2f" % sums[c]) for c in sorted(sums)]
    if out:
        sys.stdout.write("\n".join(out) + "\n")

main()

import sys
import math


def main():
    flat = sys.stdin.buffer.read().replace(b"\r", b"").replace(b"\n", b",").split(b",")
    n = (len(flat) - 3) // 3
    if n <= 0:
        return
    end = 3 + 3 * n
    cats = flat[4:end:3]
    vals = list(map(float, flat[5:end:3]))
    groups = {}
    get = groups.get
    for c, v in zip(cats, vals):
        g = get(c)
        if g is None:
            groups[c] = [v]
        else:
            g.append(v)
    out = []
    for cat in sorted(groups):
        out.append(cat.decode() + "," + ("%.2f" % math.fsum(groups[cat])))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

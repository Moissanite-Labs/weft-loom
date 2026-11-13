import sys
from collections import defaultdict


def main():
    t = sys.stdin.buffer.read().replace(b"\n", b",").split(b",")
    n = len(t) // 3 * 3
    t = t[3:n]
    sums = defaultdict(float)
    for c, v in zip(t[1::3], map(float, t[2::3])):
        sums[c] += v
    out = [k.decode() + ",%.2f" % sums[k] for k in sorted(sums)]
    if out:
        sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()

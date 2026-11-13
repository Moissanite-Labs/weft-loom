import sys
from collections import defaultdict


def main():
    data = sys.stdin.buffer
    header = data.readline()
    sums = defaultdict(float)
    get = sums.get
    for line in data:
        parts = line.rstrip(b"\r\n").split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1].decode()
        sums[cat] += float(parts[2])
    out = []
    for cat in sorted(sums):
        out.append("%s,%.2f" % (cat, sums[cat]))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

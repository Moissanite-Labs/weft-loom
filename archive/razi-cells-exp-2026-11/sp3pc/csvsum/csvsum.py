import sys
from collections import defaultdict

def main():
    lines = sys.stdin.read().splitlines()
    sums = defaultdict(float)
    for line in lines[1:]:
        p = line.split(",")
        if len(p) < 3:
            continue
        sums[p[1]] += float(p[2])
    out = ["%s,%.2f" % (c, sums[c]) for c in sorted(sums)]
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()

import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    it = iter(sys.stdin.buffer)
    next(it, None)
    for line in it:
        p = line.split(b',')
        if len(p) >= 3:
            d[p[1]] += float(p[2])
    out = ["%s,%.2f" % (k.decode(), d[k]) for k in sorted(d)]
    print("\n".join(out))
main()

import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    it = iter(sys.stdin.buffer)
    next(it, None)
    for line in it:
        p = line.split(b',')
        d[p[1]] += float(p[2])
    out = []
    for k in sorted(d):
        out.append("%s %.2f" % (k.decode(), d[k]))
    print("\n".join(out))
main()

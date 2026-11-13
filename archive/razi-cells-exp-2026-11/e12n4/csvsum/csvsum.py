import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    it = iter(sys.stdin.buffer.read().split(b'\n'))
    next(it)
    for line in it:
        if not line: continue
        p = line.split(b',')
        d[p[1]] += float(p[2])
    out = ["%s %.2f" % (k.decode(), d[k]) for k in sorted(d)]
    print("\n".join(out))
main()

import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    it = iter(sys.stdin.buffer)
    next(it)
    for line in it:
        p = line.split(b',')
        d[p[1]] += float(p[2])
    for k in sorted(d):
        print("%s %.2f" % (k.decode(), d[k]))
main()

import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    f = sys.stdin
    f.readline()
    for line in f:
        p = line.rstrip('\n').split(',')
        if len(p) >= 3:
            d[p[1]] += float(p[2])
    for k in sorted(d):
        print("%s %.2f" % (k, d[k]))
main()

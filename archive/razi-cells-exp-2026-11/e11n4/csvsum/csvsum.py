import sys
from collections import defaultdict
def main():
    d = defaultdict(float)
    f = sys.stdin.buffer
    f.readline()
    for line in f:
        p = line.split(b',')
        if len(p) >= 3:
            d[p[1]] += float(p[2])
    for k in sorted(d):
        print("%s %.2f" % (k.decode(), d[k]))
main()

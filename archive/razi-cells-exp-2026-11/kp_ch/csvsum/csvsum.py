import sys
from math import fsum
def main():
    d = {}
    data = sys.stdin.buffer.read().split(b'\n')
    for line in data[1:]:
        p = line.split(b',')
        if len(p) < 3:
            continue
        c = p[1]
        if c in d:
            d[c].append(p[2])
        else:
            d[c] = [p[2]]
    out = []
    for c in sorted(d):
        out.append("%s,%.2f" % (c.decode(), fsum(map(float, d[c]))))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))
main()

import sys
from decimal import Decimal
def main():
    d = {}
    data = sys.stdin.buffer.read().split(b'\n')
    for line in data[1:]:
        if not line:
            continue
        p = line.rstrip(b'\r').split(b',')
        c = p[1]
        v = Decimal(p[2].decode())
        d[c] = d.get(c, 0) + v
    out = []
    for c in sorted(d):
        out.append("%s,%.2f" % (c.decode(), d[c]))
    print("\n".join(out))
main()

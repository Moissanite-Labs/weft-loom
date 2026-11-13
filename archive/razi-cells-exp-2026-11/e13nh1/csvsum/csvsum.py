import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().decode().split('\n')
    d = {}
    for line in data[1:]:
        if not line:
            continue
        p = line.rstrip('\r').split(',')
        d.setdefault(p[1], []).append(p[2])
    out = []
    for k in sorted(d):
        s = sum(map(Decimal, d[k]))
        out.append("%s,%.2f" % (k, s))
    sys.stdout.write('\n'.join(out) + '\n')
main()

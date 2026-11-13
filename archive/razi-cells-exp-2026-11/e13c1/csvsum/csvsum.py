import sys
from decimal import Decimal
def main():
    d = {}
    data = sys.stdin.buffer.read().split(b'\n')
    for line in data[1:]:
        if not line:
            continue
        p = line.split(b',')
        v = p[2]
        i = v.find(b'.')
        if i < 0:
            c = int(v) * 100
        else:
            f = (v[i+1:] + b'00')[:2]
            n = v[:i]
            neg = n.startswith(b'-')
            c = abs(int(n or b'0')) * 100 + int(f)
            if neg:
                c = -c
        k = p[1]
        d[k] = d.get(k, 0) + c
    out = []
    for k in sorted(d):
        s = d[k]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (k.decode(), sg, s // 100, s % 100))
    print('\n'.join(out))
main()

import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    s = {}
    g = s.get
    for line in data[1:]:
        if not line:
            continue
        p = line.split(b',')
        v = p[2]
        i = v.find(b'.')
        c = p[1]
        if i < 0:
            n = int(v) * 100
        else:
            f = v[i+1:i+3].ljust(2, b'0')
            neg = v[:1] == b'-'
            n = int(v[:i] or b'0') * 100
            n = n - int(f) if neg else n + int(f)
        s[c] = g(c, 0) + n
    out = []
    for c in sorted(s):
        t = s[c]
        sg = '-' if t < 0 else ''
        t = abs(t)
        out.append('%s,%s%d.%02d' % (c.decode(), sg, t // 100, t % 100))
    print('\n'.join(out))
main()

import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    s = {}
    g = s.get
    for line in data[1:]:
        if not line:
            continue
        a = line.split(b',')
        c = a[1]
        v = a[2]
        i = v.find(b'.')
        if i < 0:
            n = int(v) * 100
        else:
            f = v[i+1:][:2].ljust(2, b'0')
            neg = v.startswith(b'-')
            n = int(v[:i] or b'0') * 100
            n = n - int(f) if neg else n + int(f)
        s[c] = g(c, 0) + n
    out = []
    for c in sorted(s):
        n = s[c]
        sign = '-' if n < 0 else ''
        n = abs(n)
        out.append('%s,%s%d.%02d' % (c.decode(), sign, n // 100, n % 100))
    print('\n'.join(out))
main()

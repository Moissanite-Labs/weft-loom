import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read()
    s = {}
    try:
        t = data.replace(b'\r', b'').replace(b',', b' ').replace(b'.', b'').split()[3:]
        if len(t) % 3: raise ValueError
        cats = t[1::3]; vals = list(map(int, t[2::3]))
        if data.count(b'.') != len(vals): raise ValueError
        g = s.get
        for c, v in zip(cats, vals):
            s[c] = g(c, 0) + v
        out = []
        for c in sorted(s):
            v = s[c]; sg = '-' if v < 0 else ''; v = abs(v)
            out.append('%s,%s%d.%02d' % (c.decode(), sg, v // 100, v % 100))
    except ValueError:
        s = {}
        for l in data.split(b'\n')[1:]:
            if not l.strip(): continue
            p = l.strip().split(b',')
            s[p[1]] = s.get(p[1], Decimal(0)) + Decimal(p[2].decode())
        out = ['%s,%.2f' % (c.decode(), s[c]) for c in sorted(s)]
    sys.stdout.write('\n'.join(out) + '\n')
main()

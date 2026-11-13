import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().split(b'\n')
    s = {}
    for line in data[1:]:
        if not line:
            continue
        p = line.split(b',')
        c = p[1]
        v = p[2]
        i = v.find(b'.')
        if i < 0:
            n = int(v) * 100
        else:
            f = (v[i+1:] + b'00')[:2]
            n = int(v[:i] + f) if v[:i] not in (b'', b'-') else int(v[:i] + b'0' + f) if v[:i] == b'-' else int(f)
            if v[:1] == b'-' and n > 0:
                n = -n
        s[c] = s.get(c, 0) + n
    out = []
    for c in sorted(s):
        n = s[c]
        sg = '-' if n < 0 else ''
        n = abs(n)
        out.append('%s,%s%d.%02d' % (c.decode(), sg, n // 100, n % 100))
    print('\n'.join(out))
main()

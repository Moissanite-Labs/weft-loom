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
            f = v[i+1:][:2].ljust(2, b'0')
            if v[:1] == b'-':
                c = int(v[:i] or b'0') * 100 - int(f)
                if v[:i] == b'-': c = -int(f)
            else:
                c = int(v[:i] or b'0') * 100 + int(f)
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

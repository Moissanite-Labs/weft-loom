import sys
from decimal import Decimal
def main():
    lines = sys.stdin.buffer.read().split(b'\n')
    d = {}
    g = d.get
    for ln in lines[1:]:
        if not ln:
            continue
        p = ln.split(b',')
        v = p[2]
        if v[-3:-2] == b'.':
            x = int(v.replace(b'.', b''))
        else:
            x = int(Decimal(v.decode()) * 100)
        k = p[1]
        d[k] = g(k, 0) + x
    out = []
    for k in sorted(d):
        s = d[k]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (k.decode(), sg, s // 100, s % 100))
    sys.stdout.write('\n'.join(out) + '\n')
main()

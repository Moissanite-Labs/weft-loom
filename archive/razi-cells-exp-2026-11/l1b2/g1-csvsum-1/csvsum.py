import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    d = {}
    get = d.get
    bad = False
    for ln in lines[1:]:
        if not ln:
            continue
        _, c, v = ln.split(b',', 2)
        if v[-3:-2] == b'.':
            x = int(v[:-3] + v[-2:])
        else:
            x = int(Decimal(v.decode()) * 100)
        d[c] = get(c, 0) + x
    out = []
    for c in sorted(d):
        s = d[c]
        sg = '-' if s < 0 else ''
        s = abs(s)
        out.append('%s,%s%d.%02d' % (c.decode(), sg, s // 100, s % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))
main()

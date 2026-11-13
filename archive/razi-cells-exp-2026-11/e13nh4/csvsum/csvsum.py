import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().decode().split('\n')
    d = {}
    g = d.get
    for line in data[1:]:
        if not line:
            continue
        p = line.split(',')
        c = p[1]
        v = p[2]
        i = v.find('.')
        if i >= 0 and len(v) - i == 3:
            x = int(v.replace('.', ''))
        else:
            x = int(Decimal(v.strip()) * 100)
        d[c] = g(c, 0) + x
    out = []
    for c in sorted(d):
        s = d[c]
        sign = '-' if s < 0 else ''
        s = abs(s)
        out.append("%s,%s%d.%02d" % (c, sign, s // 100, s % 100))
    print('\n'.join(out))
main()

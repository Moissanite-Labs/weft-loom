import sys
from decimal import Decimal


def cents(v):
    i = v.find(b'.')
    if i < 0:
        return int(v) * 100
    fp = v[i + 1:]
    if len(fp) == 2 and v[:1] != b'-' and fp.isdigit():
        return int(v[:i] or b'0') * 100 + int(fp)
    d = Decimal(v.decode()) * 100
    return int(d.to_integral_value())


def main():
    data = sys.stdin.buffer.read()
    sums = {}
    get = sums.get
    lines = data.split(b'\n')
    for line in lines[1:]:
        if not line:
            continue
        parts = line.split(b',', 2)
        if len(parts) < 3:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0) + cents(parts[2].strip())
    out = []
    for cat in sorted(sums):
        t = sums[cat]
        s = '-' if t < 0 else ''
        a = abs(t)
        out.append(cat.decode() + ',' + s + str(a // 100) + '.' + '%02d' % (a % 100))
    sys.stdout.write('\n'.join(out) + '\n')


main()

import sys
from decimal import Decimal


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
        v = parts[2].strip()
        d = v.find(b'.')
        if d >= 0 and len(v) - d == 3:
            try:
                c = int(v[:d] + v[d + 1:])
            except ValueError:
                c = int((Decimal(v.decode()) * 100).to_integral_value())
        elif d < 0:
            c = int(v) * 100
        else:
            c = int((Decimal(v.decode()) * 100).to_integral_value())
        sums[cat] = get(cat, 0) + c
    out = []
    for cat in sorted(sums):
        s = sums[cat]
        a = abs(s)
        out.append(cat + b',' + (b'-' if s < 0 else b'') + str(a // 100).encode() + b'.' + ('%02d' % (a % 100)).encode())
    sys.stdout.buffer.write(b'\n'.join(out) + (b'\n' if out else b''))


main()

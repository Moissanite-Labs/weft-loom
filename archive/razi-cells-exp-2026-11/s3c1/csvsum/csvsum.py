import sys
from decimal import Decimal


def cents_of(v):
    neg = v[:1] == b"-"
    if neg:
        v = v[1:]
    if b"." in v:
        ip, fp = v.split(b".", 1)
        if len(fp) <= 2:
            c = int(ip or b"0") * 100 + int((fp + b"00")[:2])
        else:
            c = int((Decimal(v.decode()) * 100).to_integral_value())
    else:
        c = int(v) * 100
    return -c if neg else c


def main():
    data = sys.stdin.buffer.read().split(b"\n")
    sums = {}
    get = sums.get
    for line in data[1:]:
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        sums[cat] = get(cat, 0) + cents_of(parts[2].strip())
    out = []
    for cat in sorted(sums):
        c = sums[cat]
        sign = "-" if c < 0 else ""
        c = abs(c)
        out.append("%s,%s%d.%02d" % (cat.decode(), sign, c // 100, c % 100))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

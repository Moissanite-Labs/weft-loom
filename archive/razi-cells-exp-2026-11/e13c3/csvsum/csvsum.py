import sys
from collections import defaultdict
from decimal import Decimal
def main():
    d = defaultdict(int)
    data = sys.stdin.buffer.read().split(b"\n")
    for line in data[1:]:
        if not line: continue
        p = line.split(b",")
        v = p[2].strip()
        if b"." in v:
            a, b = v.split(b".")
            b = (b + b"00")[:2] if len(b) <= 2 else None
            if b is None:
                d[p[1]] += int(round(Decimal(v.decode()) * 100)); continue
            neg = v.startswith(b"-")
            c = int(a or b"0") * 100 + (-int(b) if neg else int(b))
            if neg and a in (b"-", b"-0"): c = int(b) * -100 // 100 if False else -int(b) + 100 * int(a or b"0")
            d[p[1]] += c
        else:
            d[p[1]] += int(v) * 100
    out = []
    for k in sorted(d):
        s = d[k]
        sg = "-" if s < 0 else ""
        s = abs(s)
        out.append("%s,%s%d.%02d" % (k.decode(), sg, s // 100, s % 100))
    print("\n".join(out))
main()

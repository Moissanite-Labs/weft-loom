import sys
from decimal import Decimal
def main():
    data = sys.stdin.buffer.read().split(b"\n")
    d = {}
    for line in data[1:]:
        if not line:
            continue
        p = line.split(b",")
        c = p[1]
        v = p[2]
        i = v.find(b".")
        if i < 0:
            n = int(v) * 100
        else:
            f = (v[i+1:] + b"00")[:2]
            n = int(v[:i] or b"0") * 100 + int(f) if not v.startswith(b"-") else int(v[:i]) * 100 - int(f)
        d[c] = d.get(c, 0) + n
    out = []
    for c in sorted(d):
        n = d[c]
        s = "-" if n < 0 else ""
        n = abs(n)
        out.append("%s,%s%d.%02d" % (c.decode(), s, n // 100, n % 100))
    print("\n".join(out))
main()

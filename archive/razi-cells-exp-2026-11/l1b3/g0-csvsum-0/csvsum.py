import sys


def main():
    data = sys.stdin.buffer.read().split(b"\n")
    sums = {}
    get = sums.get
    for line in data[1:]:
        if not line:
            continue
        parts = line.split(b",")
        if len(parts) < 3:
            continue
        cat = parts[1]
        v = parts[2].strip().strip(b'"\r ')
        if not v:
            continue
        # value as integer cents (exact for values with <=2 decimals)
        c = round(float(v) * 100)
        sums[cat] = get(cat, 0) + c
    out = []
    for cat in sorted(sums):
        c = sums[cat]
        sign = "-" if c < 0 else ""
        c = abs(c)
        out.append("%s,%s%d.%02d" % (cat.decode(), sign, c // 100, c % 100))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

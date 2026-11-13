import sys


def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b"\n")
    del lines[0]
    sums = {}
    get = sums.get
    for line in lines:
        if not line:
            continue
        try:
            _, cat, v = line.split(b",", 2)
        except ValueError:
            continue
        v = v.strip()
        if len(v) >= 3 and v[-3] == 46:
            c = int(v[:-3] + v[-2:])
        elif b"." in v:
            ip, _, fp = v.partition(b".")
            fp = (fp + b"00")[:2]
            c = int(ip) * 100
            f = int(fp)
            c = c - f if ip.startswith(b"-") else c + f
        else:
            c = int(v) * 100
        sums[cat] = get(cat, 0) + c
    out = []
    for cat in sorted(sums):
        c = sums[cat]
        sign = "-" if c < 0 else ""
        c = abs(c)
        out.append("%s%s,%d.%02d" % (sign, cat.decode(), c // 100, c % 100))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))


main()

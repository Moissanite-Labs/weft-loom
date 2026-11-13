import sys


def main():
    data = sys.stdin.buffer.read().split(b'\n')
    sums = {}
    get = sums.get
    for line in data[1:]:
        if not line:
            continue
        parts = line.split(b',')
        if len(parts) < 3:
            continue
        cat = parts[1]
        v = parts[2].strip()
        if not v:
            continue
        c = round(float(v) * 100)
        sums[cat] = get(cat, 0) + c
    out = []
    for cat in sorted(sums):
        t = sums[cat]
        sign = '-' if t < 0 else ''
        t = abs(t)
        out.append('%s,%s%d.%02d' % (cat.decode(), sign, t // 100, t % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


main()

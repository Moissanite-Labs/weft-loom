import sys


def main():
    t = sys.stdin.buffer.read().replace(b',', b' ').split()
    totals = {}
    get = totals.get
    for cat, v in zip(t[4::3], t[5::3]):
        totals[cat] = get(cat, 0) + round(float(v) * 100)
    out = []
    for cat in sorted(totals):
        c = totals[cat]
        sign = '-' if c < 0 else ''
        c = abs(c)
        out.append('%s%s,%d.%02d' % (sign, cat.decode(), c // 100, c % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


main()

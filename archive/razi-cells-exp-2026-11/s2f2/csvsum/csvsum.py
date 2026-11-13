import sys


def main():
    data = sys.stdin.buffer.read().replace(b',', b' ').split()
    sums = {}
    get = sums.get
    n = len(data)
    i = 3
    while i + 2 < n:
        cat = data[i + 1]
        cents = round(float(data[i + 2]) * 100)
        sums[cat] = get(cat, 0) + cents
        i += 3
    out = []
    for cat in sorted(sums):
        s = sums[cat]
        sign = '-' if s < 0 else ''
        s = abs(s)
        out.append(cat.decode() + ',' + sign + str(s // 100) + '.' + '%02d' % (s % 100))
    sys.stdout.write('\n'.join(out) + '\n')


main()

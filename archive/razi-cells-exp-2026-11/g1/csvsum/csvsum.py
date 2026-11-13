import sys


def parse_cents(b):
    """Parse a decimal byte string into integer cents, rounding half up."""
    neg = False
    i = 0
    n = len(b)
    if n and b[0] == 45:  # '-'
        neg = True
        i = 1
    elif n and b[0] == 43:  # '+'
        i = 1
    dot = b.find(b'.', i)
    if dot < 0:
        cents = int(b[i:]) * 100
    else:
        ip = int(b[i:dot]) if dot > i else 0
        frac = b[dot + 1:]
        if len(frac) <= 2:
            cents = ip * 100 + int(frac.ljust(2, b'0'))
        else:
            cents = ip * 100 + int(frac[:2])
            if frac[2] >= 53:  # ord('5')
                cents += 1
    return -cents if neg else cents


def main():
    f = sys.stdin.buffer
    f.readline()  # header: id,cat,val
    sums = {}
    get = sums.get
    for line in f:
        parts = line.split(b',', 2)
        if len(parts) != 3:
            continue
        cat = parts[1]
        val = parts[2].rstrip(b'\r\n')
        c = parse_cents(val)
        sums[cat] = get(cat, 0) + c
    out = sys.stdout
    for cat in sorted(sums):
        v = sums[cat]
        sign = '-' if v < 0 else ''
        v = abs(v)
        out.write('%s,%s%d.%02d\n' % (cat.decode(), sign, v // 100, v % 100))


if __name__ == '__main__':
    main()

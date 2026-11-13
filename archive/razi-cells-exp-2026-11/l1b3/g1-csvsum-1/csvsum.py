import sys

def slow(data):
    sums = {}
    get = sums.get
    for line in data.split(b'\n')[1:]:
        if not line:
            continue
        parts = line.split(b',')
        if len(parts) < 3:
            continue
        cat = parts[1].strip()
        v = parts[2].strip()
        neg = v.startswith(b'-')
        if neg:
            v = v[1:]
        if b'.' in v:
            a, b = v.split(b'.', 1)
            b = (b + b'00')[:2]
            c = (int(a) if a else 0) * 100 + int(b)
        else:
            c = int(v) * 100 if v else 0
        if neg:
            c = -c
        sums[cat] = get(cat, 0) + c
    return sums

def main():
    data = sys.stdin.buffer.read()
    sums = None
    if b'"' not in data and b'\r' not in data and b' ' not in data:
        t = data.replace(b',', b' ').split()
        if len(t) >= 3 and len(t) % 3 == 0:
            cats = t[4::3]
            vals = t[5::3]
            sums = {}
            get = sums.get
            rnd = round
            fl = float
            for c, v in zip(cats, vals):
                sums[c] = get(c, 0) + int(rnd(fl(v) * 100))
    if sums is None:
        sums = slow(data)
    out = []
    for cat in sorted(sums):
        c = sums[cat]
        sign = '-' if c < 0 else ''
        c = abs(c)
        out.append('%s%s,%d.%02d' % (sign, cat.decode(), c // 100, c % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

main()

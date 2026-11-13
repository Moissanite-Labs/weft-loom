import sys


def cents(v):
    neg = v[:1] == b'-'
    if neg or v[:1] == b'+':
        v = v[1:]
    ip, dot, fp = v.partition(b'.')
    if len(fp) > 2 or not (ip + fp).isdigit() and (ip or fp):
        c = round(float(v) * 100)
    else:
        if not ip:
            ip = b'0'
        fp = (fp + b'00')[:2]
        c = int(ip) * 100 + int(fp)
    return -c if neg else c


def slow(raw):
    sums = {}
    get = sums.get
    for line in raw.split(b'\n')[1:]:
        if not line:
            continue
        parts = line.rstrip(b'\r').split(b',')
        if len(parts) < 3:
            continue
        cat = parts[1].strip()
        sums[cat] = get(cat, 0) + cents(parts[2].strip())
    return sums


def main():
    raw = sys.stdin.buffer.read()
    if b'"' in raw or b'\r' in raw or b' ' in raw or b'\t' in raw:
        sums = slow(raw)
    else:
        t = raw.replace(b',', b' ').split()
        if len(t) % 3 != 0 or t[:3] != [b'id', b'cat', b'val']:
            sums = slow(raw)
        else:
            cats = t[4::3]
            vals = t[5::3]
            cs = [int(v[:-3] + v[-2:]) if v[-3:-2] == b'.' else cents(v)
                  for v in vals]
            sums = {}
            get = sums.get
            for k, c in zip(cats, cs):
                sums[k] = get(k, 0) + c
    out = []
    for cat in sorted(sums):
        c = sums[cat]
        sign = '-' if c < 0 else ''
        c = abs(c)
        out.append('%s,%s%d.%02d' % (cat.decode(), sign, c // 100, c % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


main()

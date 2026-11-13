import sys, csv, io


def fmt(t):
    s = '-' if t < 0 else ''
    a = abs(t)
    return '%s%d.%02d' % (s, a // 100, a % 100)


def main():
    data = sys.stdin.buffer.read()
    d = {}
    if not (b'"' in data or b'\r' in data or b' ' in data or b'\t' in data):
        toks = data.replace(b',', b' ').split()
        if len(toks) % 3 == 0 and toks[:3] == [b'id', b'cat', b'val']:
            cats = toks[4::3]
            vals = toks[5::3]
            get = d.get
            for c, v in zip(cats, vals):
                d[c] = get(c, 0) + round(float(v) * 100)
            out = [c + b',' + fmt(d[c]).encode() + b'\n' for c in sorted(d)]
            sys.stdout.buffer.write(b''.join(out))
            return
    # slow path: general CSV
    text = data.decode('utf-8', 'replace')
    rd = csv.reader(io.StringIO(text))
    header = next(rd, None)
    for row in rd:
        if len(row) < 3:
            continue
        c = row[1].strip()
        v = row[2].strip()
        if not v:
            continue
        d[c] = d.get(c, 0) + round(float(v) * 100)
    out = [('%s,%s\n' % (c, fmt(d[c]))) for c in sorted(d)]
    sys.stdout.write(''.join(out))


if __name__ == '__main__':
    main()

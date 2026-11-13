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
        cat = parts[1].strip()
        v = parts[2].strip()
        if not cat:
            continue
        # parse value to integer cents exactly
        if b'.' in v:
            ip, _, fp = v.partition(b'.')
            fp = (fp + b'00')[:2]
            neg = ip.startswith(b'-')
            c = int(ip) * 100
            c = c - int(fp) if neg else c + int(fp)
        else:
            c = int(v) * 100
        sums[cat] = get(cat, 0) + c
    out = []
    for cat in sorted(sums):
        t = sums[cat]
        sign = '-' if t < 0 else ''
        t = abs(t)
        out.append('%s,%s%d.%02d' % (cat.decode(), sign, t // 100, t % 100))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

main()

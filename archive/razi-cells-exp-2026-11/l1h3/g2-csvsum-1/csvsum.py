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
        c = parts[1]
        v = round(float(parts[2]) * 100)
        sums[c] = get(c, 0) + v
    out = []
    for c in sorted(sums):
        s = sums[c]
        sign = '-' if s < 0 else ''
        s = abs(s)
        out.append(c.decode() + ',' + sign + '%d.%02d' % (s // 100, s % 100))
    sys.stdout.write('\n'.join(out) + '\n')

main()

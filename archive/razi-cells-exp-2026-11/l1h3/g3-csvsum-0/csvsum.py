import sys

def main():
    d = sys.stdin.buffer.read().strip().replace(b'\r', b'').replace(b'\n', b',').split(b',')
    sums = {}
    get = sums.get
    for c, v in zip(d[4::3], map(float, d[5::3])):
        sums[c] = get(c, 0) + round(v * 100)
    out = []
    for c in sorted(sums):
        s = sums[c]
        sign = '-' if s < 0 else ''
        s = abs(s)
        out.append(c.decode() + ',' + sign + '%d.%02d' % (s // 100, s % 100))
    sys.stdout.write('\n'.join(out) + '\n')

main()

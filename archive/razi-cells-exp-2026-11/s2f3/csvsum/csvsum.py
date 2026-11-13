import sys


def main():
    data = sys.stdin.buffer.read().replace(b'\r', b'').replace(b'\n', b',').split(b',')
    t = data[3:]
    if t and not t[-1]:
        t.pop()
    sums = {}
    get = sums.get
    for c, v in zip(t[1::3], t[2::3]):
        sums[c] = get(c, 0.0) + float(v)
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + ',' + ('%.2f' % sums[cat]))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


main()

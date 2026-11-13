import sys


def main():
    flat = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    sums = {}
    get = sums.get
    for c, v in zip(flat[4::3], flat[5::3]):
        sums[c] = get(c, 0.0) + float(v)
    out = [c.decode() + ',' + ('%.2f' % sums[c]) for c in sorted(sums)]
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


main()

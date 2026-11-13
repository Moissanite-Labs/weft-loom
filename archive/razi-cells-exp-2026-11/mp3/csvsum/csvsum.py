import sys


def main():
    f = sys.stdin.read().replace('\n', ',').split(',')
    cats = f[4::3]
    vals = map(float, f[5::3])
    sums = {}
    get = sums.get
    for c, v in zip(cats, vals):
        sums[c] = get(c, 0.0) + v
    out = ['%s,%.2f' % (c, sums[c]) for c in sorted(sums) if c]
    if out:
        sys.stdout.write('\n'.join(out) + '\n')


main()

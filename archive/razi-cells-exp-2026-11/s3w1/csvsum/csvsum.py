import sys


def main():
    t = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    sums = {}
    get = sums.get
    for c, v in zip(t[4::3], t[5::3]):
        if not c:
            continue
        sums[c] = get(c, 0.0) + float(v)
    out = [b'%s,%.2f' % (c, sums[c]) for c in sorted(sums)]
    if out:
        sys.stdout.buffer.write(b'\n'.join(out) + b'\n')


if __name__ == '__main__':
    main()

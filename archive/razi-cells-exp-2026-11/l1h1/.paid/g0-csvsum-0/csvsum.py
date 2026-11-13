import sys


def main():
    data = sys.stdin.buffer.read()
    sums = {}
    get = sums.get
    for line in data.split(b'\n')[1:]:
        if not line:
            continue
        parts = line.split(b',')
        if len(parts) < 3:
            continue
        cat = parts[1].rstrip(b'\r')
        v = float(parts[2])
        sums[cat] = get(cat, 0.0) + v
    out = []
    for cat in sorted(sums):
        out.append(cat.decode() + ',' + ('%.2f' % sums[cat]))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


if __name__ == '__main__':
    main()

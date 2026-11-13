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
        sums[c] = get(c, 0.0) + float(parts[2])
    out = []
    for c in sorted(sums):
        out.append(c.decode() + ',' + '%.2f' % sums[c])
    if out:
        sys.stdout.write('\n'.join(out) + '\n')


main()

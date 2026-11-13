import sys

def main():
    sums = {}
    get = sums.get
    for line in sys.stdin.buffer.read().split(b'\n')[1:]:
        p = line.split(b',')
        if len(p) < 3:
            continue
        c = p[1]
        sums[c] = get(c, 0.0) + float(p[2])
    out = [c.decode() + ',' + '%.2f' % sums[c] for c in sorted(sums)]
    if out:
        sys.stdout.write('\n'.join(out) + '\n')

main()

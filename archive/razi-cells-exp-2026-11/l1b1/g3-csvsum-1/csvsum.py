import sys

def main():
    data = sys.stdin.buffer.read()
    sums = {}
    get = sums.get
    for line in data.split(b'\n')[1:]:
        parts = line.split(b',')
        if len(parts) < 3:
            continue
        c = parts[1]
        sums[c] = get(c, 0.0) + float(parts[2])
    out = [c.decode() + ',%.2f' % sums[c] for c in sorted(sums)]
    sys.stdout.write('\n'.join(out) + '\n')

main()

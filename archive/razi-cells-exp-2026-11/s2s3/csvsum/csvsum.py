import sys
import math


def main():
    data = sys.stdin.buffer.read().split(b'\n')
    groups = {}
    for line in data[1:]:
        if not line:
            continue
        parts = line.rstrip(b'\r').split(b',')
        if len(parts) < 3:
            continue
        cat = parts[1]
        v = float(parts[2])
        g = groups.get(cat)
        if g is None:
            groups[cat] = [v]
        else:
            g.append(v)
    out = []
    for cat in sorted(groups):
        s = math.fsum(groups[cat])
        out.append(cat.decode() + ',' + ('%.2f' % s))
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))


if __name__ == '__main__':
    main()

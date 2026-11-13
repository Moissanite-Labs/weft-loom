import sys
import math


def main():
    data = sys.stdin.buffer.read().split(b'\n')
    groups = {}
    for line in data[1:]:
        if not line:
            continue
        parts = line.split(b',')
        if len(parts) < 3:
            continue
        lst = groups.get(parts[1])
        if lst is None:
            lst = groups[parts[1]] = []
        lst.append(float(parts[2]))
    out = []
    for cat in sorted(groups):
        out.append(cat.decode() + ',' + ('%.2f' % math.fsum(groups[cat])))
    if out:
        sys.stdout.write('\n'.join(out) + '\n')


main()

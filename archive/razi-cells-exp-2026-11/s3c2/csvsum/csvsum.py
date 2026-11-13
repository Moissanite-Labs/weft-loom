import sys, math
from collections import defaultdict

def main():
    data = sys.stdin.buffer.read().split(b'\n')
    groups = defaultdict(list)
    fl = float
    for line in data[1:]:
        p = line.split(b',')
        if len(p) < 3:
            continue
        try:
            v = fl(p[2])
        except ValueError:
            continue
        groups[p[1].rstrip(b'\r')].append(v)
    out = [cat.decode() + ',' + ('%.2f' % math.fsum(groups[cat])) for cat in sorted(groups)]
    sys.stdout.write('\n'.join(out) + ('\n' if out else ''))

main()

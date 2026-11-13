import sys
import math


def main():
    data = sys.stdin.buffer.read().decode()
    lines = data.split('\n')
    d = {}
    get = d.get
    for line in lines[1:]:
        if not line:
            continue
        i = line.index(',')
        j = line.index(',', i + 1)
        cat = line[i + 1:j]
        v = float(line[j + 1:])
        lst = get(cat)
        if lst is None:
            d[cat] = [v]
        else:
            lst.append(v)
    out = []
    for k in sorted(d):
        out.append('%s,%.2f' % (k, math.fsum(d[k])))
    if out:
        sys.stdout.write('\n'.join(out) + '\n')


main()

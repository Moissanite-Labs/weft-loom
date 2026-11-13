import sys
from collections import defaultdict


def main():
    data = sys.stdin.buffer.read()
    sums = {}
    nl = data.find(b'\n')
    if nl < 0:
        return
    body = data[nl + 1:]
    get = sums.get
    for line in body.split(b'\n'):
        if not line:
            continue
        if line[-1:] == b'\r':
            line = line[:-1]
        i = line.find(b',')
        j = line.find(b',', i + 1)
        if j < 0:
            continue
        cat = line[i + 1:j]
        sums[cat] = get(cat, 0.0) + float(line[j + 1:])
    out = sys.stdout
    for cat in sorted(sums):
        v = sums[cat]
        if v == 0.0:
            v = 0.0
        out.write('%s,%.2f\n' % (cat.decode(), v))


main()

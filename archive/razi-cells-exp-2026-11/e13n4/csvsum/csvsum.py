import sys
from collections import defaultdict
d = defaultdict(int)
data = sys.stdin.buffer.read().split(b'\n')
for line in data[1:]:
    if not line:
        continue
    p = line.split(b',')
    d[p[1]] += round(float(p[2]) * 100)
out = []
for k in sorted(d):
    s = d[k]
    sign = '-' if s < 0 else ''
    s = abs(s)
    out.append('%s,%s%d.%02d' % (k.decode(), sign, s // 100, s % 100))
print('\n'.join(out))

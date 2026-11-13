import sys

f = sys.stdin.buffer
f.readline()
sums = {}
get = sums.get
for line in f:
    if not line:
        continue
    p = line.split(b',')
    if len(p) < 3:
        continue
    v = p[2]
    if v[-1:] == b'\n':
        v = v[:-1]
        if v[-1:] == b'\r':
            v = v[:-1]
    if len(v) >= 4 and v[-3] == 46:
        cents = int(v.replace(b'.', b''))
    else:
        cents = int(round(float(v) * 100))
    cat = p[1]
    sums[cat] = get(cat, 0) + cents

out = sys.stdout.buffer
for cat in sorted(sums):
    t = sums[cat]
    sign = b'-' if t < 0 else b''
    if t < 0:
        t = -t
    out.write(b'%s,%s%d.%02d\n' % (cat, sign, t // 100, t % 100))

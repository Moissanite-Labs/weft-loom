import sys
import numpy as np
def main():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    a.sort()
    n = a.size
    neg = a < 0
    mag = np.abs(a)
    nd = np.ones(n, dtype=np.int64)
    mx = int(mag.max()) if n else 0
    p = 10
    maxd = 1
    while p <= mx:
        nd += mag >= p
        p *= 10
        maxd += 1
    width = nd + neg + 1
    ends = np.cumsum(width)
    buf = np.empty(int(ends[-1]) if n else 0, dtype=np.uint8)
    buf[ends - 1] = 10
    pos = ends - 2
    m = mag
    for k in range(maxd):
        if k == 0:
            buf[pos] = 48 + (m % 10)
            m = m // 10
        else:
            mask = nd > k
            sub = m[mask]
            buf[pos[mask] - k] = 48 + (sub % 10)
            m = sub // 10
            pos = pos[mask]; nd = nd[mask]
    buf[(ends - width)[neg]] = 45
    sys.stdout.buffer.write(buf.tobytes())
main()

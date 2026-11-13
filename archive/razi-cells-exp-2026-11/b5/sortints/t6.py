import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
n = a.size
neg = a < 0
m = np.abs(a)
hi, lo = np.divmod(m, 100000)
r = np.arange(100000, dtype=np.int64)
TZ = np.empty((100000, 5), np.uint8)
t = r.copy()
for j in range(4, -1, -1):
    t, d = np.divmod(t, 10)
    TZ[:, j] = d + 48
nd = np.ones(100000, np.int64)
for p in (10, 100, 1000, 10000):
    nd += r >= p
T0 = TZ.copy()
col = np.arange(5)
T0[col[None, :] < (5 - nd)[:, None]] = 32
buf = np.empty((n, 12), np.uint8)
buf[:, 0] = 32
buf[:, 11] = 10
buf[:, 1:6] = T0[hi]
buf[:, 6:11] = TZ[lo]
z = np.flatnonzero(hi == 0)
buf[z, 1:6] = 32
buf[z, 6:11] = T0[lo[z]]
ndig = np.where(hi > 0, 5 + nd[hi], nd[lo])
ni = np.flatnonzero(neg)
buf[ni, 10 - ndig[ni]] = 45
sys.stdout.buffer.write(buf.tobytes().replace(b' ', b''))

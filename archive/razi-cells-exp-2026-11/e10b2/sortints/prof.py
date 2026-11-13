import sys, time
t0=time.perf_counter()
import numpy as np
T=time.perf_counter
t1=T()
data = open('data.txt','rb').read()
t2=T()
a = np.fromstring(data, dtype=np.int64, sep=' ')
t3=T()
a.sort()
t4=T()
neg = a < 0
u = np.abs(a).astype(np.uint64)
p10 = 10 ** np.arange(1, 20, dtype=np.uint64)
nd = np.searchsorted(p10, u, side='right') + 1
ln = nd + neg + 1
ends = np.cumsum(ln)
out = np.empty(int(ends[-1]), dtype=np.uint8)
out[ends - 1] = 10
out[(ends - nd - 2)[neg]] = 45
t5=T()
pos = ends - 2
k = 1
ten = np.uint64(10)
while True:
    q = u // ten
    out[pos] = (u - q * ten).astype(np.uint8) + 48
    m = nd > k
    if not m.any():
        break
    u = q[m]; pos = pos[m] - 1; nd = nd[m]
    k += 1
t6=T()
print('import',t1-t0,'read',t2-t1,'parse',t3-t2,'sort',t4-t3,'prep',t5-t4,'digits',t6-t5)
# alt: int32 sort
b=np.fromstring(data, dtype=np.int64, sep=' ')
t=T(); c=b.astype(np.int32); c.sort(); print('i32 sort',T()-t)
t=T(); c=b.copy(); c.sort(kind='stable'); print('stable(radix?) sort',T()-t)
u=np.abs(a).astype(np.uint32)
t=T(); q=u//np.uint32(10); r=(u-q*np.uint32(10)).astype(np.uint8); print('u32 divmod',T()-t)
u=np.abs(a).astype(np.uint64)
t=T(); q=u//np.uint64(10); r=(u-q*np.uint64(10)).astype(np.uint8); print('u64 divmod',T()-t)

import sys,time
import numpy as np
T=time.perf_counter
t0=T()
data=open('data.txt','rb').read()
def swar(x):
    x = (x * 2561) >> 8
    x = ((x & 0x00ff00ff00ff00ff) * 6553601) >> 16
    x = ((x & 0x0000ffff0000ffff) * 42949672960001) >> 32
    return x
marks=[]
def m(s): marks.append((s,T()))
m('read')
data = b'\n' * 16 + data + b'\n'
L = len(data)
buf = np.frombuffer(data, np.uint8)
tok = ((buf - 48) < 10) | (buf == 45)
nws = np.count_nonzero((buf - 9) < 5) + np.count_nonzero(buf == 32)
m('classify')
b = np.flatnonzero(tok[1:] != tok[:-1])
b += 1
starts = b[0::2]
ends = b[1::2]
N = starts.size
m('bounds')
neg = buf[starts] == 45
np.count_nonzero(buf == 45) != np.count_nonzero(neg)
ln = ends - starts
nd = ln - neg
fd = buf[starts + neg]
((fd == 48) & ((nd > 1) | neg)).any()
maxd = int(nd.max())
m('checks')
view = np.ndarray(shape=(L - 7,), dtype='<u8', buffer=data, strides=(1,))
F = 0xFFFFFFFFFFFFFFFF
masks = np.array([0] + [((F << (8 * (8 - n))) & F) & 0x0f0f0f0f0f0f0f0f for n in range(1, 9)], dtype=np.uint64)
val = swar(view[ends - 8] & masks[np.minimum(nd, 8)])
if maxd > 8:
    hi = swar(view[ends - 16] & masks[np.clip(nd - 8, 0, 8)])
    val += hi * np.uint64(100000000)
val = val.astype(np.int64)
val = np.where(neg, -val, val)
m('parse')
shift = max(1, (N - 1).bit_length())
key = (val << shift) | np.arange(N, dtype=np.int64)
key.sort()
order = key & ((1 << shift) - 1)
m('sort')
ss = starts[order]
ls = ln[order]
ls += 1
cs = np.cumsum(ls)
total = int(cs[-1])
ss -= cs
ss += ls
m('out1')
src = np.repeat(ss, ls)
m('repeat')
src += np.arange(total, dtype=src.dtype)
m('arange')
out = buf[src]
m('gather')
cs -= 1
out[cs] = 10
m('nl')
p=t0
for s,t in marks:
    print(s, round((t-p)*1000,1)); p=t

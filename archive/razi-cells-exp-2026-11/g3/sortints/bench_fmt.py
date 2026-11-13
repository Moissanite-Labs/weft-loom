import numpy as np, time, warnings
warnings.filterwarnings('ignore')
D=open('test_1m.txt','rb').read()
ref=sorted(map(int,D.split()))
refout=('\n'.join(map(str,ref))+'\n').encode()

A=np.fromstring(D.decode(),dtype=np.int64,sep=' ').copy()
A.sort()
L=A.tolist()

def t(name, fn, n=3):
    best=1e9; out=None
    for _ in range(n):
        s=time.perf_counter(); o=fn(); d=time.perf_counter()-s
        best=min(best,d); out=o
    if isinstance(out,str): out=out.encode()
    print(f"{name:30s} {best*1000:8.1f} ms ok={out==refout} len={len(out) if isinstance(out,bytes) else '-'}")

t('join map str + enc', lambda: ('\n'.join(map(str,L))+'\n').encode())
def f_repr_tr():
    s=str(L)
    return s[:1]
def f_repr():
    s=str(L)
    return s.translate({91:None,93:None,44:10,32:None})+'\n'
t('str(list) translate', f_repr)
def f_repr_bytes():
    b=str(L).encode()
    return b.translate(bytes.maketrans(b'[,] ',b'\n\x00\x00\x00'))+b'\n'
def f_enc_tr():
    return (str(L)[1:-1].replace(', ','\n')+'\n').encode()
t('str slice replace enc', f_enc_tr)
def f_iota():
    # numpy digit-pair scatter
    n=L.__len__()
    a=A
    neg = a<0
    mag = np.abs(a)
    ten = np.array([1,10,100,1000,10000,100000,1000000,10000000,100000000,1000000000],dtype=np.int64)
    digits = np.searchsorted(ten, mag, side='right').astype(np.int64)
    w = digits + neg
    off = np.empty(n+1, dtype=np.int64); off[0]=0
    np.cumsum(w+1, out=off[1:])
    outb = np.empty(off[-1], dtype=np.uint8)
    base = off[:-1]
    end = base + w
    outb[end] = 10
    outb[base[neg]] = 45
    m = mag
    ar = np.arange(n)
    for j in range(5):
        q, r = np.divmod(m, 100)
        m = q
        lo, hi = np.divmod(r, 10)
        p = end - 2*(j+1)
        v = digits > 2*j
        v2 = digits > 2*j+1
        outb[p[v2]+1] = (lo[v2]+48).astype(np.uint8)
        outb[p[v]+0] = (hi[v]+48).astype(np.uint8)
    return outb.tobytes()
t('numpy pair scatter', f_iota)

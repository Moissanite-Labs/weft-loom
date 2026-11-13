import numpy as np, time, warnings
warnings.filterwarnings('ignore')
D=open('test_1m.txt','rb').read()
S=D.decode()
ref=sorted(map(int,D.split()))
refout=('\n'.join(map(str,ref))+'\n').encode()

def t(name, fn, n=3):
    best=1e9; out=None
    for _ in range(n):
        s=time.perf_counter(); o=fn(); d=time.perf_counter()-s
        best=min(best,d); out=o
    ok = out==refout
    print(f"{name:28s} {best*1000:8.1f} ms ok={ok}")

A=np.fromstring(S,dtype=np.int64,sep=' ')
print('parsed', A.shape)
for kind in ('quicksort','stable','heapsort'):
    def f(k=kind):
        b=A.copy(); b.sort(kind=k); return b
    t('sort '+kind, f)
B=A.copy(); B.sort()
L=B.tolist()
def f_join(): return '\n'.join(map(str,L))+'\n'
t('join map str', lambda: f_join().encode())
def f_repr(): return str(L)
t('str(list)', f_repr)
def f_tr():
    s=str(L)
    return s.translate({91:None,93:None,44:32}).replace(' ','\n')+'\n'
t('str(list) translate', lambda: f_tr().encode())

ten=np.array([1,10,100,1000,10000,100000,1000000,10000000,100000000,1000000000],dtype=np.uint32)
def fmt_pair(a):
    neg = (a < 0)
    mag = np.abs(a).astype(np.uint32)
    digits = np.searchsorted(ten, mag, side='right').astype(np.int64)
    w = digits + neg + 1
    off = np.empty(len(a)+1, dtype=np.int64)
    off[0]=0
    np.cumsum(w, out=off[1:])
    outb = np.empty(off[-1], dtype=np.uint8)
    base = off[:-1]
    outb[base + w - 1] = 10
    nb = w-1-neg            # bytes for digits
    if neg.any():
        outb[base[neg]] = 45
    # two-digit table
    pair = np.frombuffer(b''.join(b'%02d'%i for i in range(100)),dtype=np.uint8).reshape(100,2)
    m = mag
    # write from right in pairs
    start = base + w - 2   # position of last digit
    j = 0
    while j < 10:
        pass
    return outb.tobytes()

def fmt_digit(a):
    neg = (a < 0)
    mag = np.abs(a).astype(np.uint32)
    digits = np.searchsorted(ten, mag, side='right').astype(np.int64)
    w = digits + neg + 1
    off = np.empty(len(a)+1, dtype=np.int64)
    off[0]=0
    np.cumsum(w, out=off[1:])
    outb = np.empty(off[-1], dtype=np.uint8)
    base = off[:-1]
    outb[base + w - 1] = 10
    outb[base[neg]] = 45
    end = base + w - 2
    m = mag
    for j in range(10):
        q, r = np.divmod(m, np.uint32(10))
        m = q
        mask = digits > j
        np.copyto(outb, np.uint8(48)+r.astype(np.uint8), where=mask, casting='unsafe')
        # need positional write: do manual
        break
    return None

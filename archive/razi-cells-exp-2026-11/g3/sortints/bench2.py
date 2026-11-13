import numpy as np, time, warnings, sys
warnings.filterwarnings('ignore')
D=open('test_1m.txt','rb').read()
ref=sorted(map(int,D.split()))
refout=('\n'.join(map(str,ref))+'\n').encode()

def t(name, fn, n=3):
    best=1e9; out=None
    for _ in range(n):
        s=time.perf_counter(); o=fn(); d=time.perf_counter()-s
        best=min(best,d); out=o
    print(f"{name:24s} {best*1000:8.1f} ms ok={out==refout}")

def f_decode():
    return D.decode()
t('decode', f_decode)

def f_fromstr_bytes():
    a=np.fromstring(D.decode(),dtype=np.int64,sep=' ')
    return a
t('parse fromstring dec', f_fromstr_bytes)

def f_splitnp():
    a=np.array(D.split(),dtype=np.int64)
    return a
t('parse array(D.split)', f_splitnp)

A=np.fromstring(D.decode(),dtype=np.int64,sep=' ')
def f_sort():
    b=A.copy(); b.sort(); return b
t('np sort', f_sort)
L=A.tolist()
def f_tolist():
    return A.tolist()
t('tolist', f_tolist)
def f_join():
    return ('\n'.join(map(str,A.tolist()))+'\n').encode()
t('join tolist', f_join)
def f_join2():
    return ('\n'.join(map(str,A)))+'\n'
t('join arr(scalar str)', lambda: f_join2().encode())

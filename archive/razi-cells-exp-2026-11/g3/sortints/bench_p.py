import numpy as np, time, warnings
warnings.filterwarnings('ignore')
D=open('test_1m.txt','rb').read()
refout=open('ref_1m.bin','rb').read()

def t(name, fn, n=3):
    best=1e9; out=None
    for _ in range(n):
        s=time.perf_counter(); o=fn(); d=time.perf_counter()-s
        best=min(best,d); out=o
    print(f"{name:30s} {best*1000:8.1f} ms ok={out==refout}")

def fmt(a):
    s=str(a.tolist())
    return s.translate({91:None,93:None,44:None}).replace(' ','\n').encode()+b'\n'

def v_dec():
    a=np.fromstring(D.decode(),dtype=np.int64,sep=' ')
    a.sort(); return fmt(a)
def v_bytes():
    a=np.fromstring(D,dtype=np.int64,sep=' ')
    a.sort(); return fmt(a)
def v_splitnp():
    a=np.array(D.split(),dtype=np.int64)
    a.sort(); return fmt(a)
def v_rep():
    a=np.fromstring(D.replace(b'\n',b' '),dtype=np.int64,sep=' ')
    a.sort(); return fmt(a)
t('fromstring decode', v_dec)
t('fromstring bytes', v_bytes)
t('array(D.split)', v_splitnp)
t('fromstring replace', v_rep)

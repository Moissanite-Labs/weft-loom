import sys, time, subprocess, random

D=open('test_1m.txt','rb').read()
ref=sorted(map(int,D.split()))
refout='\n'.join(map(str,ref)).encode()+b'\n'

def check(name, fn):
    t=time.perf_counter(); out=fn(D); dt=time.perf_counter()-t
    ok = out==refout
    print(f"{name:12s} {dt*1000:8.1f} ms  ok={ok}")

def py(D):
    return ('\n'.join(map(str,sorted(map(int,D.split()))))+'\n').encode()

def np1(D):
    import numpy as np
    a=np.array(D.split(),dtype=np.int64)
    a.sort()
    return ('\n'.join(map(str,a.tolist()))+'\n').encode()

def np2(D):
    import numpy as np
    a=np.frombuffer(bytearray(D),dtype=np.uint8)
    return b'x'

check('py',py)
check('np1',np1)
import numpy as np, warnings
warnings.filterwarnings('ignore')
try:
    def np3(D):
        a=np.fromstring(D.decode(),dtype=np.int64,sep=' ')
        a.sort()
        return ('\n'.join(map(str,a.tolist()))+'\n').encode()
    check('np3',np3)
except Exception as e:
    print('np3 fail',e)

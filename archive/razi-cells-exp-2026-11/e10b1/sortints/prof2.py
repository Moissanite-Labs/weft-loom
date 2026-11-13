import time, warnings
import numpy as np
warnings.simplefilter('ignore')
data=open('data.txt','rb').read()
arr=np.fromstring(data,dtype=np.int64,sep=' ')
print('range',arr.min(),arr.max(),len(arr))
def T(name,f,n=3):
    best=1e9
    for _ in range(n):
        t=time.perf_counter(); r=f(); best=min(best,time.perf_counter()-t)
    print(name,round(best,4)); return r
T('sort64',lambda: np.sort(arr))
a32=arr.astype(np.int32)
T('sort32',lambda: np.sort(a32))
T('sort64 stable',lambda: np.sort(arr,kind='stable'))
s=np.sort(arr)
ref=T('join map str',lambda: ('\n'.join(map(str,s.tolist()))+'\n').encode('ascii'))
r2=T('%d fmt',lambda: ('%d\n'*len(s) % tuple(s.tolist())).encode('ascii'))
print(r2==ref)
r3=T('join repr',lambda: ('\n'.join(map(repr,s.tolist()))+'\n').encode('ascii'))
print(r3==ref)
r4=T('str(list) translate',lambda: str(s.tolist())[1:-1].replace(', ','\n').encode('ascii')+b'\n')
print(r4==ref)
T('tolist',lambda: s.tolist())

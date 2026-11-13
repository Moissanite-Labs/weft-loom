import time
from fibmod import f,M
a,b=0,1
for i in range(300):
    if f(i)!=a%M: print(0); raise SystemExit
    a,b=b,a+b
if f(10**18)!=209783453: print(0); raise SystemExit
t=time.time()
for i in range(20000): f(10**18-i)
print(round(20000/(time.time()-t)))

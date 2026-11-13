import time,subprocess,sys
from fibmod import fib,M
a,b=0,1
for i in range(300):
    if fib(i)!=a%M: print(0); sys.exit()
    a,b=b,a+b
if fib(10**18)!=209783453: print(0); sys.exit()
t=time.time()
for k in range(20000): fib(10**18-k)
print(round(1/(time.time()-t),3))

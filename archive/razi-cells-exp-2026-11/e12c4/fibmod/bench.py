import time,fibmod
a,b=0,1
for i in range(2000):
    if fibmod.fib(i)!=a: print(0); raise SystemExit
    a,b=b,(a+b)%fibmod.M
if fibmod.fib(10**18)!=209783453: print(0); raise SystemExit
t=time.time()
for i in range(20000): fibmod.fib(10**18-i)
print(round(20000/(time.time()-t)))

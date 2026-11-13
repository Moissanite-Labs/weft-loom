import time,fibmod
a,b=0,1
for _ in range(90):a,b=b,a+b
ok=fibmod.fib(10)==55 and fibmod.fib(90)==a%fibmod.M and fibmod.fib(10**18)==209783453
t=time.time()
for i in range(20000):fibmod.fib(10**18-i)
print(20000/(time.time()-t)/1000 if ok else 0)

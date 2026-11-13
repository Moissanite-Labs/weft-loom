import time, sys
import lcs
d=open('big.txt').read().split('\n'); a,b=d[0].rstrip('\r'),d[1].rstrip('\r')
best=0
for rep in range(7):
    t=time.perf_counter(); n=0
    while time.perf_counter()-t < 0.25:
        r=lcs.lcs_len(a,b); n+=1
        if r!=1948: print(0); sys.exit(1)
    el=time.perf_counter()-t
    best=max(best,n/el)
print(round(best,2))

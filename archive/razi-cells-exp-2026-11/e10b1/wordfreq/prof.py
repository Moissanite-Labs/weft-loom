import sys, time
from collections import Counter
_T = bytes((c if 97 <= c <= 122 else c + 32 if 65 <= c <= 90 else 32) for c in range(256))
t0=time.perf_counter()
data = open("big.txt","rb").read(); t1=time.perf_counter()
tr = data.translate(_T); t2=time.perf_counter()
sp = tr.split(); t3=time.perf_counter()
c = Counter(sp); t4=time.perf_counter()
print("read %.3f translate %.3f split %.3f count %.3f words %d uniq %d" % (t1-t0,t2-t1,t3-t2,t4-t3,len(sp),len(c)))
# alt: decode to str then split
t5=time.perf_counter()
s = tr.decode("ascii").split(); t6=time.perf_counter()
c2 = Counter(s); t7=time.perf_counter()
print("str split %.3f count %.3f" % (t6-t5,t7-t6))

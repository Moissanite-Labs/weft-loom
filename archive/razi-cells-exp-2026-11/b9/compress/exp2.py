import sys, time; sys.path.insert(0,'.')
from bench import corpus
import sq2
parts = corpus(); tin=sum(map(len,parts)); t=time.time()
tout=0
for p in parts:
    c=sq2.compress(p); assert sq2.decompress(c)==p; tout+=len(c)
print(round(tin/tout,4), time.time()-t)

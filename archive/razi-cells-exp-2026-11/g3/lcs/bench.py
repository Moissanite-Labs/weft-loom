import random, time, sys
sys.path.insert(0,'.')
from lcs import lcs_length
random.seed(7)
# 3000-char strings, moderate alphabet -> nontrivial LCS
a = bytes(random.randrange(97,97+4) for _ in range(3000))
b = bytes(random.randrange(97,97+4) for _ in range(3000))
t=time.perf_counter()
for _ in range(5):
    v=lcs_length(a,b)
dt=(time.perf_counter()-t)/5
print("lcs", v, "time", dt)

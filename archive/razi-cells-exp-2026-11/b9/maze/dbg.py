import sys, numpy as np
from collections import deque
data=sys.stdin.buffer.read().split(b'\n')
data=[l for l in data if l]
H=len(data);W=len(data[0])
g=np.frombuffer(b''.join(data),dtype=np.uint8).reshape(H,W)
print(H,W,(g==ord('S')).sum(),(g==ord('E')).sum(), (g!=ord('#')).mean())
# small python BFS from S for a limited region
print(chr(g[0,1]),chr(g[1,0]),chr(g[H-1,W-2]),chr(g[H-2,W-1]))

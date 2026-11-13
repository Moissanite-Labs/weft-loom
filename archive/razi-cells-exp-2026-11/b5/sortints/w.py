import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
np.savetxt(sys.stdout.buffer, a, fmt='%d')

import sys, os
import numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
os.write(1, ("\n".join(map(str, a.tolist())) + "\n").encode())

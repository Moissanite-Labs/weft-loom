import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
s = repr(a.tolist())
sys.stdout.write(s[1:-1].replace(', ', '\n') + '\n')

import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
sys.stdout.buffer.write(('\n'.join(map(str, a.tolist())) + '\n').encode())

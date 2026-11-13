import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
out = sys.stdout.buffer
t = a.tolist()
for i in range(0, len(t), 100000):
    out.write(('\n'.join(map(str, t[i:i+100000])) + '\n').encode())

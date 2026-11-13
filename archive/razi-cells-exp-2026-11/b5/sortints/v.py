import sys, numpy as np
a = np.array(sys.stdin.buffer.read().split(), dtype=np.int64)
a.sort()
sys.stdout.write("\n".join(map(str, a.tolist())) + "\n")

import os; os.environ["OMP_NUM_THREADS"]="1"; os.environ["OPENBLAS_NUM_THREADS"]="1"
import sys, numpy as np
a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
a.sort()
sys.stdout.buffer.write(("%d\n"*len(a) % tuple(a.tolist())).encode())

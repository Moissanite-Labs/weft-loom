import sys, warnings, numpy as np
warnings.filterwarnings('ignore')
arr = np.array(sys.stdin.buffer.read().split(), dtype=np.int64)
arr.sort()
sys.stdout.write('\n'.join(map(str, arr.tolist())))
sys.stdout.write('\n')

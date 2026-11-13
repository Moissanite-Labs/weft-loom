import sys, warnings, numpy as np
warnings.filterwarnings('ignore')
data = sys.stdin.buffer.read()
arr = np.fromstring(data, dtype=np.int64, sep=' ')
arr.sort()
sys.stdout.write('\n'.join(map(str, arr.tolist())))
sys.stdout.write('\n')

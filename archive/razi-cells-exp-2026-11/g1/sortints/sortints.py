import sys, os, warnings
os.environ.setdefault('OMP_NUM_THREADS', '1')
warnings.filterwarnings('ignore')
import numpy as np

def main():
    data = sys.stdin.buffer.read()
    if not data.strip():
        return
    arr = np.fromstring(data, dtype=np.int64, sep=' ')
    arr.sort()
    out = '\n'.join(map(str, arr.tolist()))
    sys.stdout.write(out)
    sys.stdout.write('\n')

main()

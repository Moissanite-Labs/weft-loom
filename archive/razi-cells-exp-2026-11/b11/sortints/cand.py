import sys, os
os.environ.setdefault('KMP_WARNINGS','0'); os.environ.setdefault('OMP_NUM_THREADS','1')
def main():
    data = sys.stdin.buffer.read()
    import numpy as np
    arr = np.array(data.split(), dtype=np.int64)
    arr.sort()
    sys.stdout.write('\n'.join(map(str, arr.tolist())) + '\n')
main()

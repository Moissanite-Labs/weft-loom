import sys
import numpy as np

def main():
    arr = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    arr.sort()
    sys.stdout.write('\n'.join(map(str, arr.tolist())) + '\n')

if __name__ == '__main__':
    main()

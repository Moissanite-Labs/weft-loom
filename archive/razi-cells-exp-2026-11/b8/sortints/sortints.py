import sys
import numpy as np

def main():
    data = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    data.sort()
    sys.stdout.write('\n'.join(map(str, data.tolist())) + '\n')

if __name__ == '__main__':
    main()

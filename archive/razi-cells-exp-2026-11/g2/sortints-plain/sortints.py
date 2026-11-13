import sys
import numpy as np

def main():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    a.sort()
    out = '\n'.join(map(str, a.tolist()))
    sys.stdout.write(out)
    sys.stdout.write('\n')

if __name__ == '__main__':
    main()

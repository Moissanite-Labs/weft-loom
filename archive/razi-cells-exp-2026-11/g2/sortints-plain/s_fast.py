import sys
import numpy as np

def main():
    a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    a.sort()
    out = b'\n'.join(map(b'%d'.__mod__, a.tolist()))
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.write(b'\n')

if __name__ == '__main__':
    main()

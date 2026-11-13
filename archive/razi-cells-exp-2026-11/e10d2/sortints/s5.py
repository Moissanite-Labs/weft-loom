import sys, numpy as np
def main():
    a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    a.sort()
    l = a.tolist()
    sys.stdout.buffer.write(("%d\n" * len(l) % tuple(l)).encode())
main()

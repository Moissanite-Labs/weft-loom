import sys, numpy as np
def main():
    a = np.fromstring(sys.stdin.buffer.read(), dtype=np.int64, sep=' ')
    a.sort()
    sys.stdout.buffer.write(b"\n".join(a.astype('S11').tolist()) + b"\n")
main()

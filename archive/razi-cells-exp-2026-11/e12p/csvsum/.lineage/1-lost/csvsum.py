import sys
import numpy as np
def main():
    t = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    n = (len(t)-3)//3
    c = t[4:3+3*n:3]
    v = np.array(t[5:3+3*n:3]).astype(np.float64)
    u, inv = np.unique(np.array(c), return_inverse=True)
    s = np.bincount(inv, weights=v)
    print("\n".join("%s %.2f" % (k.decode(), x) for k, x in zip(u, s)))
main()

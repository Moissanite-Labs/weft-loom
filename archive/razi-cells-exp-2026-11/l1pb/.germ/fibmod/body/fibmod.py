import sys
import numpy as np
M = 1000000007


def main():
    data = sys.stdin.read().split()
    if not data:
        print()
        return
    vals = [int(x) for x in data]
    n = np.array(vals, dtype=np.uint64)
    m = np.uint64(M)
    one = np.uint64(1)
    two = np.uint64(2)
    a = np.zeros(len(n), dtype=np.uint64)
    b = np.ones(len(n), dtype=np.uint64)
    top = max(vals).bit_length()
    for i in range(top - 1, -1, -1):
        bit = ((n >> np.uint64(i)) & one).astype(bool)
        t = a * ((two * b + m - a) % m) % m
        u = (a * a + b * b) % m
        a = np.where(bit, u, t)
        b = np.where(bit, (t + u) % m, u)
    print("\n".join(map(str, a.tolist())))


main()

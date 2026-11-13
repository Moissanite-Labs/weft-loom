import sys
import numpy as np

def main():
    data = sys.stdin.buffer.read()
    try:
        n = np.fromstring(data, dtype=np.int64, sep=' ')
    except Exception:
        n = np.array(data.split(), dtype=np.int64)
    if n.size == 0:
        return
    n = n.astype(np.uint64)
    M = np.uint64(1000000007)
    a = np.zeros(n.shape, dtype=np.uint64)
    b = np.ones(n.shape, dtype=np.uint64)
    mx = int(n.max())
    one = np.uint64(1)
    for i in range(max(mx.bit_length(), 1) - 1, -1, -1):
        t = (b << one) + M - a
        t %= M
        c = a * t % M
        d = (a * a + b * b) % M
        bit = ((n >> np.uint64(i)) & one).astype(bool)
        a = np.where(bit, d, c)
        b = np.where(bit, (c + d) % M, d)
    sys.stdout.write('\n'.join(map(str, a.tolist())) + '\n')

main()

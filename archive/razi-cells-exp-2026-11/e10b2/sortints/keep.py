import sys, numpy as np
def main():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    n = len(a)
    if n == 0:
        return
    a.sort()
    neg = a < 0
    u = np.abs(a).astype(np.uint64)
    p10 = 10 ** np.arange(1, 20, dtype=np.uint64)
    nd = np.searchsorted(p10, u, side='right') + 1
    ln = nd + neg + 1
    ends = np.cumsum(ln)
    out = np.empty(int(ends[-1]), dtype=np.uint8)
    out[ends - 1] = 10
    out[(ends - nd - 2)[neg]] = 45
    pos = ends - 2
    k = 1
    ten = np.uint64(10)
    while True:
        q = u // ten
        out[pos] = (u - q * ten).astype(np.uint8) + 48
        m = nd > k
        if not m.any():
            break
        u = q[m]; pos = pos[m] - 1; nd = nd[m]
        k += 1
    sys.stdout.buffer.write(out.data)
main()

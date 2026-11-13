import sys, numpy as np
def main():
    data = sys.stdin.buffer.read()
    a = np.fromstring(data, dtype=np.int64, sep=' ')
    n = len(a)
    if n == 0:
        return
    small = a.min() >= -2147483648 and a.max() <= 2147483647
    if small:
        a = a.astype(np.int32)
    a.sort()
    # after sorting, numbers with same sign and digit count are contiguous
    cuts = [1 - 10 ** k for k in range(18, -1, -1)] + [10 ** k for k in range(1, 19)]
    idx = [0] + a.searchsorted(np.array(cuts, dtype=np.int64)).tolist() + [n]
    groups = []
    total = 0
    for g in range(38):
        lo = idx[g]; hi = idx[g + 1]
        if hi > lo:
            if g < 19:
                nd = 19 - g; neg = 1
            else:
                nd = g - 18; neg = 0
            groups.append((lo, hi, nd, neg, total))
            total += (hi - lo) * (nd + neg + 1)
    out = np.empty(total, dtype=np.uint8)
    for lo, hi, nd, neg, off in groups:
        c = hi - lo
        w = nd + neg + 1
        blk = out[off:off + c * w].reshape(c, w)
        blk[:, w - 1] = 10
        v = a[lo:hi]
        if neg:
            blk[:, 0] = 45
            v = -v
        if nd <= 9 or small:
            u = v.astype(np.uint32); ten = np.uint32(10); z = np.uint32(48)
        else:
            u = v.astype(np.uint64); ten = np.uint64(10); z = np.uint64(48)
        col = w - 2
        while True:
            if col == neg:
                blk[:, col] = u + z
                break
            q = u // ten
            blk[:, col] = u - q * ten + z
            u = q
            col -= 1
    sys.stdout.buffer.write(out.data)
main()

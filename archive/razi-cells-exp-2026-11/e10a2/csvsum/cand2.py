import sys, os
T = int(os.environ.get('T', '4'))
MM = int(os.environ.get('MM', '1'))
def slow(data):
    from collections import defaultdict
    d = defaultdict(float)
    for line in data.split(b'\n')[1:]:
        line = line.strip()
        if line:
            _, c, v = line.split(b',')
            d[c] += float(v)
    return ''.join(['%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)])
def chunk(np, buf, data, lo, hi, res, i):
    b = buf[lo:hi]
    seps = np.flatnonzero(b < 45)
    n3 = seps.size
    if n3 == 0 or n3 % 3:
        return
    if not (b[seps].reshape(-1, 3) == np.array([44, 44, 10], dtype=np.uint8)).all():
        return
    c1 = seps[0::3]; c2 = seps[1::3]; e = seps[2::3]
    rows = e.size
    if not (b[e - 3] == 46).all():
        return
    neg = b[c2 + 1] == 45
    nd = e - c2 - 4 - neg
    mn = int(nd.min()); mx = int(nd.max())
    if mn < 1 or mx > 9:
        return
    t = b[e - 1] - 48
    bad = t > 9
    cents = t.astype(np.int64)
    t = b[e - 2] - 48
    bad |= t > 9
    cents += t * np.int64(10)
    mul = 100
    for k in range(mx):
        t = b[e - (4 + k)] - 48
        if k >= mn:
            t = np.where(nd > k, t, 0).astype(np.uint8)
        bad |= t > 9
        cents += t * np.int64(mul)
        mul *= 10
    if bad.any():
        return
    cents = np.where(neg, -cents, cents)
    L = c2 - c1 - 1
    L0 = int(L[0])
    if L0 < 1 or L0 > 32 or not (L == L0).all():
        return
    idx = None; total = 1
    for j in range(L0):
        col = b[c1 + (1 + j)]
        if (col == col[0]).all():
            continue
        present = np.flatnonzero(np.bincount(col, minlength=256))
        r = present.size
        lut = np.zeros(256, dtype=np.intp)
        lut[present] = np.arange(r)
        total *= r
        if total > (1 << 20):
            return
        idx = lut[col] if idx is None else idx * r + lut[col]
    if idx is None:
        idx = np.zeros(rows, dtype=np.intp)
    sums = np.bincount(idx, weights=cents, minlength=total)
    ex = np.full(total, -1, dtype=np.int64)
    ex[idx] = np.arange(rows)
    d = {}
    for k in np.flatnonzero(ex >= 0).tolist():
        a = lo + int(c1[int(ex[k])]) + 1
        d[bytes(data[a:a + L0])] = int(sums[k])
    res[i] = d
def fast(data):
    import numpy as np
    n = len(data)
    if n == 0 or data[n - 1:n] != b'\n':
        return None
    h = data.find(b'\n') + 1
    if h >= n:
        return None
    buf = np.frombuffer(data, dtype=np.uint8)
    nt = T if n - h > (1 << 20) else 1
    bounds = [h]
    for i in range(1, nt):
        p = data.find(b'\n', h + (n - h) * i // nt) + 1
        if p > bounds[-1] and p < n:
            bounds.append(p)
    bounds.append(n)
    m = len(bounds) - 1
    res = [None] * m
    if m == 1:
        chunk(np, buf, data, bounds[0], bounds[1], res, 0)
    else:
        import threading
        ths = [threading.Thread(target=chunk, args=(np, buf, data, bounds[i], bounds[i + 1], res, i)) for i in range(1, m)]
        for th in ths: th.start()
        chunk(np, buf, data, bounds[0], bounds[1], res, 0)
        for th in ths: th.join()
    tot = {}
    for d in res:
        if d is None:
            return None
        for k, v in d.items():
            tot[k] = tot.get(k, 0) + v
    out = []
    for k in sorted(tot):
        v = tot[k]
        sg = '-' if v < 0 else ''
        v = abs(v)
        out.append('%s,%s%d.%02d\n' % (k.decode(), sg, v // 100, v % 100))
    return ''.join(out)
def main():
    data = None
    if MM:
        try:
            import mmap
            if os.lseek(0, 0, 1) == 0:
                data = mmap.mmap(0, 0, access=mmap.ACCESS_READ)
        except Exception:
            data = None
    if data is None:
        data = sys.stdin.buffer.read()
    res = None
    try:
        res = fast(data)
    except Exception:
        res = None
    if res is None:
        res = slow(data[:])
    sys.stdout.write(res)
main()

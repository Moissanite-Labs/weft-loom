import sys
def slow(data):
    from collections import defaultdict
    d = defaultdict(float)
    for line in data.split(b'\n')[1:]:
        line = line.strip()
        if line:
            _, c, v = line.split(b',')
            d[c] += float(v)
    return ''.join(['%s,%.2f\n' % (k.decode(), d[k]) for k in sorted(d)])
def fast(data):
    import numpy as np
    if b'\r' in data or b'"' in data or not data.endswith(b'\n'):
        return None
    buf = np.frombuffer(data, dtype=np.uint8)
    nl = np.flatnonzero(buf == 10)
    cm = np.flatnonzero(buf == 44)
    if nl.size < 2 or cm.size != 2 * nl.size:
        return None
    c1 = cm[2::2]; c2 = cm[3::2]; e = nl[1:]; s = nl[:-1]
    if not ((c1 > s).all() and (c2 < e).all()):
        return None
    rows = e.size
    # values: [-]D+.DD
    if not (buf[e - 3] == 46).all():
        return None
    neg = buf[c2 + 1] == 45
    nd = e - c2 - 4 - neg
    mn = int(nd.min()); mx = int(nd.max())
    if mn < 1 or mx > 9:
        return None
    t = buf[e - 1] - 48
    bad = t > 9
    cents = t.astype(np.int64)
    t = buf[e - 2] - 48
    bad |= t > 9
    cents += t * np.int64(10)
    mul = 100
    for k in range(mx):
        t = buf[e - (4 + k)] - 48
        if k >= mn:
            m = nd > k
            t = np.where(m, t, 0).astype(np.uint8)
        bad |= t > 9
        cents += t * np.int64(mul)
        mul *= 10
    if bad.any():
        return None
    cents = np.where(neg, -cents, cents)
    # categories: fixed length, mixed-radix compact index
    L = c2 - c1 - 1
    L0 = int(L[0])
    if L0 < 1 or L0 > 32 or not (L == L0).all():
        return None
    idx = None; total = 1
    for j in range(L0):
        col = buf[c1 + (1 + j)]
        present = np.flatnonzero(np.bincount(col, minlength=256))
        r = present.size
        if r == 1:
            continue
        lut = np.zeros(256, dtype=np.intp)
        lut[present] = np.arange(r)
        total *= r
        if total > (1 << 20):
            return None
        idx = lut[col] if idx is None else idx * r + lut[col]
    if idx is None:
        idx = np.zeros(rows, dtype=np.intp)
    sums = np.bincount(idx, weights=cents, minlength=total)
    ex = np.full(total, -1, dtype=np.int64)
    ex[idx] = np.arange(rows)
    out = []
    c1l = c1; 
    for b in range(total):
        r = int(ex[b])
        if r < 0:
            continue
        a = int(c1[r]) + 1
        name = data[a:a + L0].decode()
        v = int(sums[b])
        sg = '-' if v < 0 else ''
        v = abs(v)
        out.append('%s,%s%d.%02d\n' % (name, sg, v // 100, v % 100))
    return ''.join(out)
def main():
    data = sys.stdin.buffer.read()
    res = None
    try:
        res = fast(data)
    except Exception:
        res = None
    if res is None:
        res = slow(data)
    sys.stdout.write(res)
main()

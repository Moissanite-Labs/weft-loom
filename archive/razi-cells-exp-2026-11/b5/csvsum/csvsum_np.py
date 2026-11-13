import sys
import numpy as np

def main():
    buf = sys.stdin.buffer.read()
    h = buf.index(b'\n') + 1
    a = np.frombuffer(buf, dtype=np.uint8)[h:]
    n = len(a)
    if n == 0:
        return
    if a[-1] != 10:
        a = np.concatenate((a, np.array([10], np.uint8)))
        n += 1
    nl = np.flatnonzero(a == 10)
    comma = np.flatnonzero(a == 44)
    c1 = comma[0::2]
    c2 = comma[1::2]
    # --- values: c2+1 .. nl
    vlen = nl - c2 - 1
    maxw = int(vlen.max())
    ar = np.arange(maxw)
    idx = c2[:, None] + 1 + ar
    np.minimum(idx, n - 1, out=idx)
    ch = a[idx]
    valid = ar < vlen[:, None]
    neg = ch[:, 0] == 45
    isdig = valid & (ch >= 48) & (ch <= 57)
    ndig = isdig.sum(1)
    rank = np.cumsum(isdig, axis=1) - 1
    power = (ndig[:, None] - 1 - rank).astype(np.int64)
    pw = np.int64(10) ** np.arange(maxw + 1, dtype=np.int64)
    np.maximum(power, 0, out=power)
    d = (ch.astype(np.int64) - 48) * pw[power]
    d[~isdig] = 0
    cents = d.sum(1)
    cents[neg] = -cents[neg]
    # --- keys: c1+1 .. c2
    klen = c2 - c1 - 1
    maxk = int(klen.max())
    kw = max(maxk, 1)
    ark = np.arange(kw)
    kidx = c1[:, None] + 1 + ark
    np.minimum(kidx, n - 1, out=kidx)
    kch = a[kidx]
    kch[ark >= klen[:, None]] = 0
    if kw <= 8:
        pad = np.zeros((len(kch), 8), np.uint8)
        pad[:, :kw] = kch
        keys = pad.view(np.uint64).ravel()
        uk, inv = np.unique(keys, return_inverse=True)
        names = [uk.view(np.uint8)[i*8:(i+1)*8].tobytes().rstrip(b'\0').decode() for i in range(len(uk))]
    else:
        keys = np.ascontiguousarray(kch).view('S%d' % kw).ravel()
        uk, inv = np.unique(keys, return_inverse=True)
        names = [k.decode() for k in uk.tolist()]
    sums = np.bincount(inv, weights=cents.astype(np.float64), minlength=len(uk))
    out = []
    order = sorted(range(len(names)), key=lambda i: names[i])
    for i in order:
        c = int(round(sums[i]))
        sign = '-' if c < 0 else ''
        c = abs(c)
        out.append("%s,%s%d.%02d\n" % (names[i], sign, c // 100, c % 100))
    sys.stdout.write(''.join(out))

main()

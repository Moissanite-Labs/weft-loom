import sys

def slow(buf):
    from collections import defaultdict
    sums = defaultdict(float)
    lines = buf.decode('ascii', 'replace').split('\n')
    start = 1 if lines and lines[0].startswith('id,') else 0
    for ln in lines[start:]:
        if not ln:
            continue
        _, c, v = ln.split(',', 2)
        sums[c] += float(v)
    return [(c, "%.2f" % sums[c]) for c in sorted(sums)]

def fast(buf):
    import numpy as np
    a = np.frombuffer(buf, dtype=np.uint8)
    if a[-1] != 10:
        return None
    nl = np.flatnonzero(a == 10)
    hdr_end = nl[0]
    if buf[:hdr_end] != b'id,cat,val':
        return None
    nl = nl[1:]                      # line ends of data rows
    n = len(nl)
    commas = np.flatnonzero(a[hdr_end:] == 44) + hdr_end
    if len(commas) != 2 * n:
        return None
    commas = commas.reshape(n, 2)
    c1 = commas[:, 0]; c2 = commas[:, 1]
    starts = np.empty(n, dtype=np.int64); starts[0] = hdr_end + 1; starts[1:] = nl[:-1] + 1
    if not (np.all(c1 > starts) and np.all(c2 > c1) and np.all(nl > c2)):
        return None
    # ---- values: require form [-]digits.dd (exactly two decimals) -> exact int cents
    vlen = nl - c2 - 1
    L = int(vlen.max())
    if L > 18 or vlen.min() < 4:
        return None
    idx = (c2[:, None] + 1 + np.arange(L, dtype=np.int64)[None, :])
    idx = np.minimum(idx, len(a) - 1)
    ch = a[idx]                      # (n, L) chars, garbage beyond line end
    rel = np.arange(L)[None, :]
    valid = rel < vlen[:, None]
    neg = ch[:, 0] == 45
    # dot must be at position vlen-3
    dotpos = vlen - 3
    if not np.all(a[c2 + 1 + dotpos] == 46):
        return None
    isdigit = (ch >= 48) & (ch <= 57)
    digpos = valid & (rel != dotpos[:, None]) & ~((rel == 0)[None, :] & neg[:, None]) if False else None
    # positions that must be digits: all valid except the dot and leading '-'
    first = neg.astype(np.int64)
    must = valid & (rel != dotpos[:, None]) & (rel >= first[:, None])
    if not np.all(isdigit[must]):
        return None
    if not np.all(dotpos > first):
        return None
    # exponent of each digit position in cents: cents weight = 10**(dotpos - rel - 1 + 2) for rel<dotpos, 10**(dotpos+2-rel) for rel>dotpos
    e = np.where(rel < dotpos[:, None], dotpos[:, None] - rel + 1, dotpos[:, None] + 2 - rel)
    e = np.where(must, e, -1)
    pow10 = np.concatenate(([0], 10 ** np.arange(0, 20, dtype=np.int64)))  # index -1 -> 0? handle via e+1
    w = pow10[e + 1]
    d = (ch.astype(np.int64) - 48) * w
    cents = d.sum(axis=1)
    cents = np.where(neg, -cents, cents)
    # ---- categories: fixed-width padded bytes
    clen = c2 - c1 - 1
    Lc = int(clen.max())
    if Lc == 0 or Lc > 64:
        return None
    cidx = np.minimum(c1[:, None] + 1 + np.arange(Lc, dtype=np.int64)[None, :], len(a) - 1)
    cch = a[cidx]
    cch = np.where(np.arange(Lc)[None, :] < clen[:, None], cch, 0).astype(np.uint8)
    keys = np.ascontiguousarray(cch).view('S%d' % Lc).ravel()
    uniq, inv = np.unique(keys, return_inverse=True)
    sums = np.bincount(inv, weights=cents.astype(np.float64), minlength=len(uniq))
    out = []
    for k, s in zip(uniq.tolist(), sums.tolist()):
        s = int(round(s))
        sign = '-' if s < 0 else ''
        s = abs(s)
        out.append((k.decode('ascii'), "%s%d.%02d" % (sign, s // 100, s % 100)))
    return out

def main():
    buf = sys.stdin.buffer.read()
    res = None
    try:
        res = fast(buf)
    except Exception:
        res = None
    if res is None:
        res = slow(buf)
    sys.stdout.write("".join("%s,%s\n" % (c, v) for c, v in res))

main()

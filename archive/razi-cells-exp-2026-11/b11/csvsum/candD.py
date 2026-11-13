import sys, os, pickle
import numpy as np
from itertools import compress
NW = int(os.environ.get("NW", "4"))

def slow(body):
    flat = body.replace(b"\n", b",").split(b",")
    cats = flat[1::3]; vals = flat[2::3]
    d = {}
    for c in set(cats):
        d[c] = int(round(sum(map(float, compress(vals, map(c.__eq__, cats)))) * 100))
    return d

def fast(body):
    a = np.frombuffer(body, np.uint8)
    n_ = len(a)
    nl = np.flatnonzero(a == 10)
    if len(nl) == 0: return None
    starts = np.empty_like(nl); starts[0] = 0; starts[1:] = nl[:-1] + 1
    commas = np.flatnonzero(a == 44)
    if len(commas) != 2 * len(nl): return None
    c1 = commas[0::2]; c2 = commas[1::2]
    if not ((c1 > starts).all() and (c2 > c1 + 1).all() and (nl > c2 + 1).all()): return None
    cs = c1 + 1; clen = c2 - cs; W = int(clen.max())
    if W > 32: return None
    ar = np.arange(W)
    win = a[np.minimum(cs[:, None] + ar, n_ - 1)]
    win[ar >= clen[:, None]] = 0
    h = np.zeros(len(nl), np.int64)
    for j in range(W):
        h = h * 1000003 + win[:, j]
    uh, first, inv = np.unique(h, return_index=True, return_inverse=True)
    inv = inv.ravel()
    if not (win == win[first][inv]).all(): return None
    vs = c2 + 1; vlen = nl - vs; V = int(vlen.max())
    if V > 20: return None
    ar = np.arange(V)
    vw = a[np.minimum(vs[:, None] + ar, n_ - 1)]
    vw[ar >= vlen[:, None]] = 32
    isdig = (vw >= 48) & (vw <= 57)
    dot = vw == 46
    if not ((dot.sum(1) == 1).all() and (dot[np.arange(len(nl)), vlen - 3]).all()): return None
    neg = vw[:, 0] == 45
    ok = isdig | dot | (vw == 32)
    ok[:, 0] |= neg
    if not ok.all(): return None
    after = (isdig[:, ::-1].cumsum(1, dtype=np.int8)[:, ::-1] - isdig)
    cents = np.zeros(len(nl), np.int64)
    p10 = 10 ** np.arange(21, dtype=np.int64)
    for j in range(V):
        cents += (vw[:, j].astype(np.int64) - 48) * isdig[:, j] * p10[after[:, j]]
    cents = np.where(neg, -cents, cents)
    sums = np.bincount(inv, weights=cents.astype(np.float64), minlength=len(uh))
    sums = np.rint(sums).astype(np.int64)
    return {bytes(win[i]).rstrip(b"\x00"): int(sums[k]) for k, i in enumerate(first)}

def compute(body):
    if not body: return {}
    d = fast(body)
    if d is None: d = slow(body)
    return d

def main():
    data = sys.stdin.buffer.read()
    nl = data.find(b"\n")
    body = data[nl+1:].strip(b"\n") if nl >= 0 else b""
    total = {}
    if body:
        body = body + b"\n"
        n = len(body)
        bounds = [0]
        for i in range(1, NW):
            p = body.find(b"\n", n * i // NW)
            p = n if p < 0 else p + 1
            bounds.append(max(p, bounds[-1]))
        bounds.append(n)
        chunks = [body[bounds[i]:bounds[i+1]] for i in range(NW)]
        pipes = []
        for ch in chunks[1:]:
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                try:
                    res = pickle.dumps(compute(ch))
                except Exception:
                    res = pickle.dumps(None)
                with os.fdopen(w, "wb") as f: f.write(res)
                os._exit(0)
            os.close(w)
            pipes.append((pid, r))
        total = dict(compute(chunks[0]))
        for pid, r in pipes:
            with os.fdopen(r, "rb") as f: res = pickle.loads(f.read())
            os.waitpid(pid, 0)
            if res is None: res = compute(body); total = {}; 
            for k, v in res.items(): total[k] = total.get(k, 0) + v
    out = []
    for c in sorted(total):
        v = total[c]; sign = "-" if v < 0 else ""; v = abs(v)
        out.append(f"{c.decode()},{sign}{v // 100}.{v % 100:02d}\n")
    sys.stdout.write("".join(out))
main()

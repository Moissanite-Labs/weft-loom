import sys
def main():
    data = sys.stdin.buffer.read()
    nl = data.index(b'\n')
    body = data[nl+1:]
    if body.endswith(b'\n'): body = body[:-1]
    cols = body.replace(b'\n', b',').split(b',')
    cats = cols[1::3]; vals = cols[2::3]
    try:
        import numpy as np
        v = np.fromstring(b','.join(vals), sep=',', dtype=np.float64)
        if len(v) != len(vals): raise ValueError
        k = np.array(cats)
        u, inv = np.unique(k, return_inverse=True)
        s = np.bincount(inv, weights=v, minlength=len(u))
        out = ["%s,%.2f" % (c.decode(), x) for c, x in zip(u.tolist(), s.tolist())]
    except Exception:
        from collections import defaultdict
        d = defaultdict(float)
        for c, x in zip(cats, vals): d[c] += float(x)
        out = ["%s,%.2f" % (c.decode(), d[c]) for c in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()

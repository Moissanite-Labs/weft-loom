import sys
def main():
    data = sys.stdin.buffer.read().replace(b'\n', b',').split(b',')
    while data and data[-1] == b'': data.pop()
    cats = data[4::3]
    vals = data[5::3]
    try:
        import numpy as np
        v = np.array(vals).astype(np.float64)
        u, inv = np.unique(np.array(cats), return_inverse=True)
        s = np.bincount(inv, weights=v)
        out = ["%s,%.2f" % (k.decode(), x) for k, x in zip(u, s)]
    except ImportError:
        d = {}
        for c, x in zip(cats, vals):
            d[c] = d.get(c, 0.0) + float(x)
        out = ["%s,%.2f" % (k.decode(), d[k]) for k in sorted(d)]
    sys.stdout.write("\n".join(out) + "\n")
main()

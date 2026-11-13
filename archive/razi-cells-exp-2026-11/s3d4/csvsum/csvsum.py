import sys
from math import fsum

def main():
    data = sys.stdin.buffer.read()
    if b'\r' in data:
        data = data.replace(b'\r', b'')
    t = data.replace(b'\n', b',').split(b',')
    # t[0:3] is header 'id,cat,val'; then rows of (id, cat, val)
    cats = t[4::3]
    vals = t[5::3]
    d = {}
    get = d.get
    for c, v in zip(cats, vals):
        if not c:
            continue
        l = get(c)
        if l is None:
            d[c] = [v]
        else:
            l.append(v)
    out = []
    for c in sorted(d):
        out.append("%s,%.2f" % (c.decode(), fsum(map(float, d[c]))))
    sys.stdout.write("\n".join(out) + ("\n" if out else ""))

main()

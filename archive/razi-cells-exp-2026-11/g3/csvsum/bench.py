import time
data = open('data.csv','rb').read()

def A(data):
    i = data.index(b'\n')
    lines = data[i+1:].split(b'\n')
    sums = {}
    g = sums.get
    for ln in lines:
        if not ln: continue
        a = ln.find(b',')
        b = ln.rfind(b',')
        cat = ln[a+1:b]
        v = int(ln[b+1:].replace(b'.', b''))
        sums[cat] = g(cat, 0) + v
    return sums

def D(data):
    i = data.index(b'\n')
    lines = data[i+1:].split(b'\n')
    sums = {}
    g = sums.get
    for ln in lines:
        if not ln: continue
        a = ln.find(b',')
        b = ln.rfind(b',')
        cat = ln[a+1:b]
        sums[cat] = g(cat, 0) + int(ln[b+1:].replace(b'.', b''))
    return sums

def F(data):
    # translate-dot then split all at once
    i = data.index(b'\n')
    rest = data[i+1:].replace(b'.', b'').replace(b'\n', b',')
    f = rest.split(b',')
    sums = {}
    g = sums.get
    cats = f[1::3]; vals = f[2::3]
    for c, v in zip(cats, vals):
        sums[c] = g(c, 0) + int(v)
    return sums

exp = {}
for line in open('expected.txt'):
    c, v = line.split()
    neg = v.startswith('-')
    v = v.lstrip('-')
    a, b = v.split('.')
    exp[c.encode()] = (int(a)*100+int(b)) * (-1 if neg else 1)

def fmt(sums):
    out = []
    for c in sorted(sums):
        v = sums[c]
        sign = '-' if v < 0 else ''
        v = abs(v)
        out.append(b"%s %s%d.%02d\n" % (c, sign.encode(), v//100, v%100))
    return b"".join(out)

for name, fn in [('A', A), ('D', D), ('F', F)]:
    best = 9e9
    for _ in range(3):
        t = time.perf_counter(); s = fn(data); dt = time.perf_counter()-t
        best = min(best, dt)
    ok = (fmt(s) == open('expected.txt','rb').read())
    print(name, "%.3f" % best, "ok" if ok else "WRONG")

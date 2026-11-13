import os, time, pickle, sys
data = open('data.csv','rb').read()
exp = open('expected.txt','rb').read()

def core(body):
    if b'\r' in body:
        body = body.replace(b'\r', b'')
    t = body.replace(b'.', b'').replace(b'\n', b',')
    f = t.split(b',')
    sums = {}
    get = sums.get
    cats = f[1::3]; vals = f[2::3]
    for c, v in zip(cats, vals):
        sums[c] = get(c, 0) + int(v)
    return sums

def split_body(data):
    nl = data.find(b'\n')
    return data[nl+1:]

def fmt(sums):
    out = []
    for c in sorted(sums):
        v = sums[c]
        if v < 0:
            v = -v; out.append(b"%s -%d.%02d\n" % (c, v//100, v%100))
        else:
            out.append(b"%s %d.%02d\n" % (c, v//100, v%100))
    return b"".join(out)

def parallel(body, n):
    L = len(body)
    if n <= 1 or L == 0:
        return core(body)
    bounds = [0]
    for i in range(1, n):
        p = L*i//n
        q = body.find(b'\n', p)
        bounds.append(L if q < 0 else q+1)
    bounds.append(L)
    pipes = []; pids = []
    for i in range(n):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                d = pickle.dumps(core(body[bounds[i]:bounds[i+1]]), 2)
                os.write(w, d)
            finally:
                os.close(w)
                os._exit(0)
        os.close(w)
        pipes.append(r); pids.append(pid)
    sums = {}
    g = sums.get
    for r in pipes:
        chunks = []
        while True:
            b = os.read(r, 1 << 16)
            if not b: break
            chunks.append(b)
        os.close(r)
        for k, v in pickle.loads(b''.join(chunks)).items():
            sums[k] = g(k, 0) + v
    for pid in pids:
        os.waitpid(pid, 0)
    return sums

body = split_body(data)
for n in (1,2,3,4,6,8):
    best = 9e9; ok = None
    for _ in range(3):
        t = time.perf_counter(); s = parallel(body, n); dt = time.perf_counter()-t
        best = min(best, dt); ok = fmt(s) == exp
    print(n, "%.4f" % best, "ok" if ok else "WRONG")

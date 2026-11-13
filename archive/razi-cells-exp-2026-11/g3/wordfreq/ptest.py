import os, sys, time, pickle
from collections import Counter

data = open('corpus.txt','rb').read()
exp = open('expected.txt').read()

TBL = bytes((c+32 if 65<=c<=90 else c) if (97<=c<=122 or 65<=c<=90) else 32 for c in range(256))
LOW = data.translate(TBL)

def top(c):
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return ''.join('%s %d\n' % (k.decode(), v) for k, v in items)

def cuts(t, k):
    n = len(t); step = n // k; pos = 0; b = []
    for i in range(k-1):
        j = min(pos + step, n)
        while j < n and t[j] != 32: j += 1
        b.append((pos, j)); pos = j
    b.append((pos, n))
    return b

def par(k):
    pids = []; rs = []
    for a, b in cuts(LOW, k):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(r)
                d = {}
                for tok in LOW[a:b].split():
                    d[tok] = d.get(tok, 0) + 1
                with os.fdopen(w, 'wb') as f:
                    pickle.dump(d, f, 5)
            finally:
                os._exit(0)
        os.close(w); pids.append(pid); rs.append(r)
    tot = Counter()
    for r in rs:
        with os.fdopen(r, 'rb') as f:
            tot.update(pickle.load(f))
    for pid in pids: os.waitpid(pid, 0)
    return tot

def tm(f, n=5):
    best = 9e9; res = None
    for _ in range(n):
        s = time.perf_counter(); res = f(); dt = time.perf_counter()-s
        if dt < best: best = dt
    return best, res

b, r = tm(lambda: top(Counter(LOW.split())))
print('seq', round(b,4), top(Counter(LOW.split())) == exp)
for k in (4, 8, 10):
    b, r = tm(lambda k=k: top(par(k)))
    print('par', k, round(b,4), top(r) == exp, 'MB/s', round(len(data)/b/1e6,1))

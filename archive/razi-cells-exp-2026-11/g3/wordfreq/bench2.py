import os, sys, time, pickle
from collections import Counter

data = open('corpus.txt','rb').read()
exp = open('expected.txt').read()

TBL = bytes((c+32 if 65<=c<=90 else c) if (97<=c<=122 or 65<=c<=90) else 32 for c in range(256))

def top(c,):
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return ''.join('%s %d\n' % (k.decode(), v) for k, v in items)

# seq
def seq():
    t = data.translate(TBL)
    c = Counter(p for p in t.split() if p)
    return top(c)

# parallel via fork + pickle through pipes
def par(k):
    t = data.translate(TBL)
    n = len(t)
    bounds = []
    pos = 0
    step = n // k
    for i in range(k-1):
        j = pos + step
        while j < n and t[j] != 32:
            j += 1
        bounds.append((pos, j)); pos = j
    bounds.append((pos, n))
    pids = []
    pipes = []
    for a, b in bounds:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(r)
                c = Counter(p for p in t[a:b].split() if p)
                with os.fdopen(w, 'wb') as f:
                    pickle.dump(c, f, 5)
            finally:
                os._exit(0)
        os.close(w)
        pids.append(pid); pipes.append(r)
    tot = Counter()
    for r in pipes:
        with os.fdopen(r, 'rb') as f:
            tot.update(pickle.load(f))
    for pid in pids:
        os.waitpid(pid, 0)
    return top(tot)

def tm(f, n=5):
    best = 9e9
    for _ in range(n):
        s = time.perf_counter(); res = f(); dt = time.perf_counter()-s
        best = min(best, dt)
    return best, res

b, r = tm(seq); print('seq', round(b,4), r == exp)
for k in (2,4,6,8,10):
    b, r = tm(lambda k=k: par(k)); print('par', k, round(b,4), r == exp, 'MB/s', round(len(data)/b/1e6,1))
python3 -c "print(open('/dev/null').read())"

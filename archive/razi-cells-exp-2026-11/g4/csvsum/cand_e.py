import sys, os, pickle
import numpy as np
def parse(chunk):
    toks = chunk.replace(b',', b' ').split()
    ca = np.array(toks[1::3])
    va = np.array(toks[2::3], dtype=np.float64)
    L = ca.dtype.itemsize
    if L <= 8:
        v = ca.view(np.uint8).reshape(-1, L)
        key = np.zeros(len(ca), dtype=np.uint64)
        for k in range(L):
            key = (key << np.uint64(8)) | v[:, k].astype(np.uint64)
        u, first, inv = np.unique(key, return_index=True, return_inverse=True)
        sums = np.bincount(inv, weights=va, minlength=len(u))
        names = ca[first]
    else:
        names, inv = np.unique(ca, return_inverse=True)
        sums = np.bincount(inv, weights=va, minlength=len(names))
    return list(names), sums
def main():
    data = sys.stdin.buffer.read()
    i = data.find(b'\n') + 1
    body = data[i:]
    n = len(body)
    W = min(8, os.cpu_count() or 1)
    jobs = []
    start = 0
    for k in range(1, W):
        p = body.find(b'\n', n * k // W)
        if p < 0: p = n
        jobs.append((start, p))
        start = p + 1
        if start >= n: break
    jobs.append((start, n))
    procs = []
    for s, e in jobs:
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                out = pickle.dumps(parse(body[s:e]), protocol=4)
            except BaseException:
                os._exit(1)
            with os.fdopen(w, 'wb') as f:
                f.write(out)
            os._exit(0)
        os.close(w)
        procs.append((r, pid))
    total = {}
    for r, pid in procs:
        with os.fdopen(r, 'rb') as f:
            u, sums = pickle.load(f)
        os.waitpid(pid, 0)
        for c, v in zip(u, sums):
            total[c] = total.get(c, 0.0) + v
    sys.stdout.write('\n'.join(c.decode()+','+format(total[c],'.2f') for c in sorted(total))+'\n')
main()

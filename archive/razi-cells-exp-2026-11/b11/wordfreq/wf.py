import sys, os, pickle
from collections import Counter
TBL = bytearray(b' ' * 256)
for ch in b"abcdefghijklmnopqrstuvwxyz0123456789'":
    TBL[ch] = ch
for ch in b"ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    TBL[ch] = ch + 32
TBL = bytes(TBL)
def count(data, start, end):
    c = Counter()
    upd = c.update
    step = 1 << 21
    while start < end:
        e = min(start + step, end)
        if e < end:
            j = data.rfind(b'\n', start, e)
            if j > start:
                e = j
        upd(data[start:e].translate(TBL).split())
        start = e
    return c
def main():
    data = sys.stdin.buffer.read()
    n = len(data)
    nw = min(os.cpu_count() or 1, 8)
    if nw < 2 or n < (1 << 20):
        c = count(data, 0, n)
    else:
        bounds = [0]
        for i in range(1, nw):
            p = n * i // nw
            j = data.find(b'\n', p)
            bounds.append(n if j < 0 else j + 1)
        bounds.append(n)
        procs = []
        for i in range(nw):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                c = count(data, bounds[i], bounds[i + 1])
                with os.fdopen(w, 'wb') as f:
                    pickle.dump(dict(c), f, protocol=pickle.HIGHEST_PROTOCOL)
                os._exit(0)
            os.close(w)
            procs.append((pid, r))
        c = Counter()
        for pid, r in procs:
            with os.fdopen(r, 'rb') as f:
                c.update(pickle.load(f))
            os.waitpid(pid, 0)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join(f"{w.decode()} {n}\n" for w, n in top))
main()

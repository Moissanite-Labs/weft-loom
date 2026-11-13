import sys, os, marshal
from collections import Counter

K = 4
T = bytearray(b' ' * 256)
for _i in range(26):
    T[97 + _i] = 97 + _i
    T[65 + _i] = 97 + _i
T = bytes(T)

def main():
    data = sys.stdin.buffer.read()
    n = len(data)
    k = K
    if n < (1 << 16) or not hasattr(os, 'fork'):
        k = 1
    bounds = [0]
    for i in range(1, k):
        p = n * i // k
        while p < n and T[data[p]] != 32:
            p += 1
        bounds.append(p)
    bounds.append(n)
    pipes = []
    for i in range(1, k):
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            code = 1
            try:
                os.close(r)
                d = dict(Counter(data[bounds[i]:bounds[i + 1]].translate(T).split()))
                with os.fdopen(w, 'wb') as f:
                    marshal.dump(d, f)
                code = 0
            finally:
                os._exit(code)
        os.close(w)
        pipes.append((pid, r))
    c = Counter(data[bounds[0]:bounds[1]].translate(T).split())
    get = c.get
    for pid, r in pipes:
        with os.fdopen(r, 'rb') as f:
            d = marshal.load(f)
        os.waitpid(pid, 0)
        for w_, cnt in d.items():
            c[w_] = get(w_, 0) + cnt
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write("".join("%s %d\n" % (w.decode(), n) for w, n in top))

main()

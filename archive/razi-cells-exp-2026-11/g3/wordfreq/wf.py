import os
import sys
import pickle
from collections import Counter

TBL = bytes((c + 32 if 65 <= c <= 90 else c) if (97 <= c <= 122 or 65 <= c <= 90) else 32
             for c in range(256))
K = 6


def render(c):
    items = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return ''.join('%s %d\n' % (k.decode(), v) for k, v in items)


def run(t):
    n = len(t)
    if n < 400000 or not hasattr(os, 'fork'):
        sys.stdout.write(render(Counter(t.split())))
        return
    bounds = []
    pos = 0
    step = n // K
    for _ in range(K - 1):
        j = pos + step
        while j < n and t[j] != 32:
            j += 1
        bounds.append((pos, j))
        pos = j
    bounds.append((pos, n))
    pipes = []
    pids = []
    for a, b in bounds:
        if b <= a:
            continue
        r, w = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            try:
                c = Counter(t[a:b].split())
                with os.fdopen(w, 'wb') as f:
                    pickle.dump(c, f, 5)
            except BaseException:
                os._exit(1)
            os._exit(0)
        os.close(w)
        pipes.append(r)
        pids.append(pid)
    tot = Counter()
    for r in pipes:
        with os.fdopen(r, 'rb') as f:
            tot.update(pickle.load(f))
    for pid in pids:
        os.waitpid(pid, 0)
    sys.stdout.write(render(tot))


def main():
    run(sys.stdin.buffer.read().translate(TBL))


main()

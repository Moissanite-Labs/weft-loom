import sys
import numpy as np
def main():
    data = sys.stdin.buffer.read()
    rows = data.split()
    if not rows:
        print(-1); return
    h = len(rows); w = len(rows[0])
    joined = b''.join(rows)
    if len(joined) != h * w:
        rows = [r[:w].ljust(w, b'#') for r in rows]; joined = b''.join(rows)
    si = joined.find(b'S'); ei = joined.find(b'E')
    if si < 0 or ei < 0:
        print(-1); return
    W = w + 2
    g = np.zeros((h + 2, W), np.bool_)
    np.not_equal(np.frombuffer(joined, np.uint8).reshape(h, w), 35, out=g[1:h+1, 1:w+1])
    g = g.reshape(-1)
    s = (si // w + 1) * W + si % w + 1
    e = (ei // w + 1) * W + ei % w + 1
    if s == e:
        print(0); return
    g[s] = False
    f = np.array([s], np.intp)
    d = 0
    cat = np.concatenate
    take = g.take
    put = g.put
    offs = (-1, 1, -W, W)
    while True:
        d += 1
        parts = []
        for o in offs:
            nb = f + o
            nb = nb.compress(take(nb))
            if nb.size:
                put(nb, False)
                parts.append(nb)
        n = len(parts)
        if n == 0:
            break
        if not g[e]:
            print(d); return
        f = parts[0] if n == 1 else cat(parts)
    print(-1)
main()

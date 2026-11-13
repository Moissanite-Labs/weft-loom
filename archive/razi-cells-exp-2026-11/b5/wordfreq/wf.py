#!/usr/bin/env python3
import sys, os, pickle
from collections import Counter

TBL = None

def count(buf):
    return Counter(buf.translate(TBL).decode('latin-1').split())

def main():
    global TBL
    tbl = bytearray(b' ' * 256)
    for i in range(97, 123):
        tbl[i] = i
        tbl[i - 32] = i
    TBL = bytes(tbl)
    data = sys.stdin.buffer.read()
    n = len(data)
    W = max(1, min(8, os.cpu_count() or 1))
    if n < 1 << 20 or W < 2 or not hasattr(os, 'fork'):
        c = count(data)
    else:
        bounds = [0]
        for k in range(1, W):
            p = n * k // W
            while p < n and TBL[data[p]] != 32:
                p += 1
            bounds.append(p)
        bounds.append(n)
        pipes = []
        for k in range(1, W):
            r, w = os.pipe()
            pid = os.fork()
            if pid == 0:
                os.close(r)
                out = pickle.dumps(dict(count(data[bounds[k]:bounds[k+1]])), protocol=pickle.HIGHEST_PROTOCOL)
                with os.fdopen(w, 'wb') as f:
                    f.write(out)
                os._exit(0)
            os.close(w)
            pipes.append((pid, r))
        c = count(data[bounds[0]:bounds[1]])
        for pid, r in pipes:
            with os.fdopen(r, 'rb') as f:
                c.update(pickle.load(f))
            os.waitpid(pid, 0)
    top = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    sys.stdout.write(''.join('%s %d\n' % kv for kv in top))

if __name__ == '__main__':
    main()

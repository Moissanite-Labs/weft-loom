import sys
import numpy as np

def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    lines = [l.rstrip(b'\r') for l in lines]
    lines = [l for l in lines if l]
    if not lines:
        print(-1); return
    H = len(lines); W = max(len(l) for l in lines)
    buf = np.full((H, W), ord('#'), dtype=np.uint8)
    for i, l in enumerate(lines):
        buf[i, :len(l)] = np.frombuffer(l, dtype=np.uint8)
    s = np.argwhere(buf == ord('S'))
    e = np.argwhere(buf == ord('E'))
    if len(s) == 0 or len(e) == 0:
        print(-1); return
    Wp = W + 2
    # padded flat arrays with wall border
    free = np.zeros((H + 2, W + 2), dtype=bool)
    free[1:-1, 1:-1] = buf != ord('#')
    free = free.ravel()
    sidx = (s[0][0] + 1) * Wp + s[0][1] + 1
    eidx = (e[0][0] + 1) * Wp + e[0][1] + 1
    if sidx == eidx:
        print(0); return
    free[sidx] = False
    frontier = np.array([sidx], dtype=np.int64)
    d = 0
    offs = (1, -1, Wp, -Wp)
    while frontier.size:
        d += 1
        nxt = []
        for o in offs:
            c = frontier + o
            c = c[free[c]]
            if c.size:
                free[c] = False
                nxt.append(c)
        if not nxt:
            break
        frontier = np.concatenate(nxt) if len(nxt) > 1 else nxt[0]
        if not free[eidx]:
            print(d); return
    print(-1)

main()

import sys
import numpy as np

def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    lines = [l.rstrip(b'\r') for l in lines]
    H = len(lines)
    if H == 0:
        print(-1); return
    W = max(len(l) for l in lines)
    if W == 0:
        print(-1); return
    if all(len(l) == W for l in lines):
        g = np.frombuffer(b''.join(lines), dtype=np.uint8).reshape(H, W)
    else:
        g = np.full((H, W), ord('#'), dtype=np.uint8)
        for i, l in enumerate(lines):
            g[i, :len(l)] = np.frombuffer(l, dtype=np.uint8)
    PW = W + 2
    unvisited = np.zeros((H + 2) * PW, dtype=bool)
    unvisited.reshape(H + 2, PW)[1:-1, 1:-1] = g != 35
    s = np.flatnonzero(g == 83)
    e = np.flatnonzero(g == 69)
    if len(s) == 0 or len(e) == 0:
        print(-1); return
    sr, sc = divmod(int(s[0]), W)
    er, ec = divmod(int(e[0]), W)
    start = (sr + 1) * PW + (sc + 1)
    end = (er + 1) * PW + (ec + 1)
    if start == end:
        print(0); return
    unvisited[start] = False
    frontier = np.array([start], dtype=np.int64)
    d = 0
    offs = (1, -1, PW, -PW)
    while frontier.size:
        d += 1
        parts = []
        for o in offs:
            nb = frontier + o
            nb = nb[unvisited[nb]]
            if nb.size:
                unvisited[nb] = False
                parts.append(nb)
        if not parts:
            break
        if not unvisited[end]:
            print(d); return
        frontier = np.concatenate(parts) if len(parts) > 1 else parts[0]
    print(-1)

main()

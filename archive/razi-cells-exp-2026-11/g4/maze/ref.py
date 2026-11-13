import sys
from collections import deque
from array import array

def main():
    data = sys.stdin.buffer.read()
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    lines = [ln[:-1] if ln.endswith(b'\r') else ln for ln in lines]
    if not lines:
        print(-1); return
    w = max(len(ln) for ln in lines)
    h = len(lines)
    if w == 0:
        print(-1); return
    stride = w + 2
    total = (h + 2) * stride
    g = bytearray(b'#' * total)
    s = e = -1
    for y, ln in enumerate(lines):
        base = (y + 1) * stride + 1
        for x, c in enumerate(ln):
            if c == 83:
                g[base + x] = 46
                if s < 0: s = base + x
            elif c == 69:
                g[base + x] = 46
                if e < 0: e = base + x
            elif c == 46:
                g[base + x] = 46
    if s < 0 or e < 0:
        print(-1); return
    dist = array('i', [-1]) * total
    dist[s] = 0
    q = deque([s])
    st = stride
    ans = -1
    while q:
        cur = q.popleft()
        if cur == e:
            ans = dist[cur]; break
        d = dist[cur] + 1
        for nb in (cur-1, cur+1, cur-st, cur+st):
            if g[nb] == 46 and dist[nb] < 0:
                dist[nb] = d
                q.append(nb)
    print(ans)

if __name__ == '__main__':
    main()

import sys
from collections import deque
def ref(data):
    g = [l for l in data.decode().split("\n") if l]
    h = len(g)
    s = e = None
    for y in range(h):
        for x, c in enumerate(g[y]):
            if c == 'S': s = (y, x)
            if c == 'E': e = (y, x)
    if s is None or e is None: return -1
    dist = {s: 0}; dq = deque([s])
    while dq:
        y, x = dq.popleft()
        if (y, x) == e: return dist[(y, x)]
        for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < h and 0 <= nx < len(g[ny]) and g[ny][nx] != '#' and (ny, nx) not in dist:
                dist[(ny, nx)] = dist[(y, x)] + 1; dq.append((ny, nx))
    return -1
if __name__ == "__main__":
    print(ref(sys.stdin.buffer.read()))

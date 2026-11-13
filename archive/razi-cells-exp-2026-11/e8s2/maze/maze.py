import sys
from collections import deque

def solve():
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    if b'\r' in data:
        data = data.replace(b'\r\n', b'\n')
    if not data.endswith(b'\n'):
        data += b'\n'
    
    s = data.find(b'S')
    e = data.find(b'E')
    if s == -1 or e == -1:
        print(-1)
        return
    if s == e:
        print(0)
        return

    w = data.find(b'\n')
    stride = w + 1
    
    pad = b'#' * stride
    grid = bytearray(pad + data + pad)
    s += stride
    e += stride
    
    grid[s] = 35
    grid[e] = 46
    
    q = deque([s])
    popleft = q.popleft
    append = q.append
    dist = 0
    while q:
        dist += 1
        for _ in range(len(q)):
            u = popleft()
            v = u - 1
            if grid[v] == 46:
                if v == e:
                    print(dist)
                    return
                grid[v] = 35
                append(v)
            v = u + 1
            if grid[v] == 46:
                if v == e:
                    print(dist)
                    return
                grid[v] = 35
                append(v)
            v = u - stride
            if grid[v] == 46:
                if v == e:
                    print(dist)
                    return
                grid[v] = 35
                append(v)
            v = u + stride
            if grid[v] == 46:
                if v == e:
                    print(dist)
                    return
                grid[v] = 35
                append(v)
    print(-1)

if __name__ == '__main__':
    solve()

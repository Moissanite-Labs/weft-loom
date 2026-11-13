import sys
from collections import deque

def solve():
    data = sys.stdin.buffer.read()
    lines = data.splitlines()
    if not lines:
        print(-1)
        return
    
    H = len(lines)
    W = len(lines[0])
    
    # Pad with '#' by adding a border or using stride W + 1 (since lines are separated by \n in raw data, wait: splitlines removes \n, or we can use raw data if uniform width!)
    # Let's check if raw data has uniform line length or just build a padded bytearray
    stride = W + 2
    grid = bytearray(b'#' * (stride * (H + 2)))
    
    start = -1
    end = -1
    
    for r, line in enumerate(lines):
        offset = (r + 1) * stride + 1
        grid[offset:offset+W] = line
        if start == -1:
            s_idx = line.find(b'S')
            if s_idx != -1:
                start = offset + s_idx
        if end == -1:
            e_idx = line.find(b'E')
            if e_idx != -1:
                end = offset + e_idx
                
    if start == -1 or end == -1:
        print(-1)
        return
    if start == end:
        print(0)
        return
        
    grid[start] = 35 # '#'
    grid[end] = 46   # '.' so we only check for '.' (46)
    
    q = deque([start])
    dist = 0
    
    while q:
        dist += 1
        for _ in range(len(q)):
            u = q.popleft()
            
            v = u - 1
            if grid[v] == 46:
                if v == end:
                    print(dist)
                    return
                grid[v] = 35
                q.append(v)
                
            v = u + 1
            if grid[v] == 46:
                if v == end:
                    print(dist)
                    return
                grid[v] = 35
                q.append(v)
                
            v = u - stride
            if grid[v] == 46:
                if v == end:
                    print(dist)
                    return
                grid[v] = 35
                q.append(v)
                
            v = u + stride
            if grid[v] == 46:
                if v == end:
                    print(dist)
                    return
                grid[v] = 35
                q.append(v)
                
    print(-1)

if __name__ == '__main__':
    solve()

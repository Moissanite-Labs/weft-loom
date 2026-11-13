import sys
from collections import deque

def solve():
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    lines = data.splitlines()
    H = len(lines)
    if H == 0:
        print(-1)
        return
    W = len(lines[0])
    stride = W + 1
    # Ensure newline separated uniform buffer or build bytearray
    s_pos = data.find(b'S')
    e_pos = data.find(b'E')
    if s_pos == -1 or e_pos == -1:
        print(-1)
        return
    
    # Standard 2D BFS for baseline correctness
    grid = [bytearray(line) for line in lines]
    sr, sc = divmod(s_pos, stride)
    er, ec = divmod(e_pos, stride)
    if grid[sr][sc] != ord('S'):
        # fallback search if line endings are \r\n or irregular
        for r, row in enumerate(grid):
            c = row.find(b'S')
            if c != -1:
                sr, sc = r, c
            c2 = row.find(b'E')
            if c2 != -1:
                er, ec = r, c2
    if (sr, sc) == (er, ec):
        print(0)
        return
    
    q = deque([(sr, sc, 0)])
    grid[sr][sc] = 35 # '#'
    grid[er][ec] = 46 # '.'
    
    while q:
        r, c, d = q.popleft()
        nd = d + 1
        if r > 0 and grid[r-1][c] == 46:
            if r-1 == er and c == ec:
                print(nd)
                return
            grid[r-1][c] = 35
            q.append((r-1, c, nd))
        if r + 1 < H and grid[r+1][c] == 46:
            if r+1 == er and c == ec:
                print(nd)
                return
            grid[r+1][c] = 35
            q.append((r+1, c, nd))
        if c > 0 and grid[r][c-1] == 46:
            if r == er and c-1 == ec:
                print(nd)
                return
            grid[r][c-1] = 35
            q.append((r, c-1, nd))
        if c + 1 < W and grid[r][c+1] == 46:
            if r == er and c+1 == ec:
                print(nd)
                return
            grid[r][c+1] = 35
            q.append((r, c+1, nd))
    print(-1)

if __name__ == '__main__':
    solve()

import sys

def solve():
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    s_pos = data.find(b'S')
    e_pos = data.find(b'E')
    if s_pos == -1 or e_pos == -1:
        print(-1)
        return
    if s_pos == e_pos:
        print(0)
        return
    nl = data.find(b'\n')
    W = (nl + 1) if nl != -1 else (len(data) + 1)

    grid = bytearray(data)
    grid.extend(b'#' * (W + 2))
    # Bidirectional BFS:
    # '.' = 46, visited from S = 1, visited from E = 2
    grid[s_pos] = 1
    grid[e_pos] = 2

    front_s = [s_pos]
    front_e = [e_pos]
    dist = 0
    neg_W = -W
    while front_s and front_e:
        dist += 1
        if len(front_s) <= len(front_e):
            nxt = []
            append = nxt.append
            for u in front_s:
                v = u - 1
                c = grid[v]
                if c == 46:
                    grid[v] = 1
                    append(v)
                elif c == 2:
                    print(dist)
                    return
                v = u + 1
                c = grid[v]
                if c == 46:
                    grid[v] = 1
                    append(v)
                elif c == 2:
                    print(dist)
                    return
                v = u + neg_W
                c = grid[v]
                if c == 46:
                    grid[v] = 1
                    append(v)
                elif c == 2:
                    print(dist)
                    return
                v = u + W
                c = grid[v]
                if c == 46:
                    grid[v] = 1
                    append(v)
                elif c == 2:
                    print(dist)
                    return
            front_s = nxt
        else:
            nxt = []
            append = nxt.append
            for u in front_e:
                v = u - 1
                c = grid[v]
                if c == 46:
                    grid[v] = 2
                    append(v)
                elif c == 1:
                    print(dist)
                    return
                v = u + 1
                c = grid[v]
                if c == 46:
                    grid[v] = 2
                    append(v)
                elif c == 1:
                    print(dist)
                    return
                v = u + neg_W
                c = grid[v]
                if c == 46:
                    grid[v] = 2
                    append(v)
                elif c == 1:
                    print(dist)
                    return
                v = u + W
                c = grid[v]
                if c == 46:
                    grid[v] = 2
                    append(v)
                elif c == 1:
                    print(dist)
                    return
            front_e = nxt
    print(-1)

if __name__ == '__main__':
    solve()

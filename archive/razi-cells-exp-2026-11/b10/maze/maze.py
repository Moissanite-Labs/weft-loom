import sys

def solve():
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    if b'\r' in data:
        data = data.replace(b'\r\n', b'\n')
    
    s_pos = data.find(b'S')
    e_pos = data.find(b'E')
    if s_pos == -1 or e_pos == -1:
        print(-1)
        return
    if s_pos == e_pos:
        print(0)
        return

    nl = data.find(b'\n')
    W = (len(data) + 1) if nl == -1 else (nl + 1)

    pad = b'#' * W
    grid = bytearray(pad + data + pad)
    if grid[len(pad) + len(data) - 1] != 10:
        grid.extend(pad)
    
    start = s_pos + W
    end = e_pos + W
    grid[start] = 36 # forward visited
    grid[end] = 47   # backward visited

    fq = [start]
    bq = [end]
    dist = 0
    while fq and bq:
        dist += 1
        if len(fq) <= len(bq):
            nxt = []
            append = nxt.append
            for u in fq:
                v = u - 1
                if grid[v] >= 46:
                    if grid[v] == 46:
                        grid[v] = 36
                        append(v)
                    else:
                        print(dist); return
                v = u + 1
                if grid[v] >= 46:
                    if grid[v] == 46:
                        grid[v] = 36
                        append(v)
                    else:
                        print(dist); return
                v = u - W
                if grid[v] >= 46:
                    if grid[v] == 46:
                        grid[v] = 36
                        append(v)
                    else:
                        print(dist); return
                v = u + W
                if grid[v] >= 46:
                    if grid[v] == 46:
                        grid[v] = 36
                        append(v)
                    else:
                        print(dist); return
            fq = nxt
        else:
            nxt = []
            append = nxt.append
            for u in bq:
                v = u - 1
                if grid[v] >= 36:
                    if grid[v] == 46:
                        grid[v] = 47
                        append(v)
                    elif grid[v] == 36:
                        print(dist); return
                v = u + 1
                if grid[v] >= 36:
                    if grid[v] == 46:
                        grid[v] = 47
                        append(v)
                    elif grid[v] == 36:
                        print(dist); return
                v = u - W
                if grid[v] >= 36:
                    if grid[v] == 46:
                        grid[v] = 47
                        append(v)
                    elif grid[v] == 36:
                        print(dist); return
                v = u + W
                if grid[v] >= 36:
                    if grid[v] == 46:
                        grid[v] = 47
                        append(v)
                    elif grid[v] == 36:
                        print(dist); return
            bq = nxt
    print(-1)

if __name__ == '__main__':
    solve()

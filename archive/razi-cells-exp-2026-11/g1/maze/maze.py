import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        sys.stdout.write('-1\n')
        return
    H = len(data)
    W = max(len(r) for r in data)
    PW = W + 2
    buf = bytearray(b'#' * (PW * (H + 2)))
    S = -1
    E = -1
    for r in range(H):
        row = data[r]
        base = (r + 1) * PW + 1
        buf[base:base + len(row)] = row
        j = row.find(b'S')
        if j >= 0:
            S = base + j
        j = row.find(b'E')
        if j >= 0:
            E = base + j
    if S < 0 or E < 0:
        sys.stdout.write('-1\n')
        return
    WALL = 35  # ord('#')
    up = -PW
    dn = PW
    buf[S] = WALL
    frontier = [S]
    dist = 0
    while frontier:
        dist += 1
        nxt = []
        ap = nxt.append
        for i in frontier:
            n = i + up
            if buf[n] != WALL:
                if n == E:
                    sys.stdout.write(str(dist) + '\n')
                    return
                buf[n] = WALL
                ap(n)
            n = i + dn
            if buf[n] != WALL:
                if n == E:
                    sys.stdout.write(str(dist) + '\n')
                    return
                buf[n] = WALL
                ap(n)
            n = i - 1
            if buf[n] != WALL:
                if n == E:
                    sys.stdout.write(str(dist) + '\n')
                    return
                buf[n] = WALL
                ap(n)
            n = i + 1
            if buf[n] != WALL:
                if n == E:
                    sys.stdout.write(str(dist) + '\n')
                    return
                buf[n] = WALL
                ap(n)
        frontier = nxt
    sys.stdout.write('-1\n')

main()

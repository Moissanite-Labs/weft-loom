import sys


def solve(data):
    rows = data.split()
    if not rows:
        return -1
    H = len(rows)
    W = len(rows[0])
    W2 = W + 2
    grid = bytearray(b'#' * (W2 * (H + 2)))
    s = e = -1
    for i, row in enumerate(rows):
        base = (i + 1) * W2 + 1
        grid[base:base + W] = row[:W]
        if s < 0:
            j = row.find(b'S')
            if j >= 0:
                s = base + j
        if e < 0:
            j = row.find(b'E')
            if j >= 0:
                e = base + j
    if s < 0 or e < 0:
        return -1
    grid[s] = 35
    frontier = [s]
    d = 0
    W2n = -W2
    while frontier:
        nxt = []
        append = nxt.append
        d1 = d + 1
        for p in frontier:
            q = p - 1
            if grid[q] != 35:
                if q == e:
                    return d1
                grid[q] = 35
                append(q)
            q = p + 1
            if grid[q] != 35:
                if q == e:
                    return d1
                grid[q] = 35
                append(q)
            q = p - W2
            if grid[q] != 35:
                if q == e:
                    return d1
                grid[q] = 35
                append(q)
            q = p + W2
            if grid[q] != 35:
                if q == e:
                    return d1
                grid[q] = 35
                append(q)
        frontier = nxt
        d = d1
    return -1


def main():
    data = sys.stdin.buffer.read()
    print(solve(data))


if __name__ == "__main__":
    main()

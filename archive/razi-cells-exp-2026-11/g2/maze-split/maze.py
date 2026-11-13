import sys


def main():
    data = sys.stdin.buffer.read()
    rows = data.splitlines()
    while rows and not rows[-1]:
        rows.pop()
    if not rows:
        sys.stdout.write("-1\n")
        return
    h = len(rows)
    w = len(rows[0])
    stride = w + 2
    total = (h + 2) * stride
    grid = bytearray([1]) * total

    tbl = bytearray([1]) * 256
    tbl[ord('.')] = 0
    tbl[ord('S')] = 0
    tbl[ord('E')] = 0
    table = bytes(tbl)

    s = e = -1
    for y in range(h):
        row = rows[y]
        base = (y + 1) * stride + 1
        i = row.find(b'S')
        if i >= 0:
            s = base + i
        i = row.find(b'E')
        if i >= 0:
            e = base + i
        grid[base:base + len(row)] = row.translate(table)

    if s < 0 or e < 0:
        sys.stdout.write("-1\n")
        return
    if s == e:
        sys.stdout.write("0\n")
        return

    grid[s] = 1
    frontier = [s]
    dist = 0
    while frontier:
        dist += 1
        nxt = []
        ap = nxt.append
        for p in frontier:
            q = p - 1
            if not grid[q]:
                if q == e:
                    sys.stdout.write(str(dist) + "\n")
                    return
                grid[q] = 1
                ap(q)
            q = p + 1
            if not grid[q]:
                if q == e:
                    sys.stdout.write(str(dist) + "\n")
                    return
                grid[q] = 1
                ap(q)
            q = p - stride
            if not grid[q]:
                if q == e:
                    sys.stdout.write(str(dist) + "\n")
                    return
                grid[q] = 1
                ap(q)
            q = p + stride
            if not grid[q]:
                if q == e:
                    sys.stdout.write(str(dist) + "\n")
                    return
                grid[q] = 1
                ap(q)
        frontier = nxt
    sys.stdout.write("-1\n")


main()

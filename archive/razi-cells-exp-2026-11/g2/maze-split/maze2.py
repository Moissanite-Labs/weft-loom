import sys


def solve():
    data = sys.stdin.buffer.read()
    rows = data.replace(b'\r', b'').split(b'\n')
    while rows and not rows[-1]:
        rows.pop()
    if not rows:
        return "-1"
    w = len(rows[0])
    if any(len(r) != w for r in rows):
        rows = [r.ljust(w, b'#') if len(r) < w else r[:w] for r in rows]
    h = len(rows)
    stride = w + 1  # trailing '\n' becomes a wall column
    tbl = bytearray([1]) * 256
    tbl[46] = 0   # .
    tbl[83] = 0   # S
    tbl[69] = 0   # E
    table = bytes(tbl)
    src = b'\n'.join(rows) + b'\n'
    si = src.find(b'S')
    ei = src.find(b'E')
    if si < 0 or ei < 0:
        return "-1"
    s = si + stride
    e = ei + stride
    if s == e:
        return "0"
    grid = bytearray(b'\x01' * stride) + src.translate(table) + b'\x01' * stride
    grid[s] = 1
    q = [s, -1]
    head = 0
    dist = 0
    while True:
        p = q[head]
        head += 1
        if p < 0:
            if head >= len(q):
                return "-1"
            dist += 1
            q.append(-1)
            continue
        nd = dist + 1
        ap = q.append
        x = p - 1
        if not grid[x]:
            if x == e:
                return str(nd)
            grid[x] = 1
            ap(x)
        x = p + 1
        if not grid[x]:
            if x == e:
                return str(nd)
            grid[x] = 1
            ap(x)
        x = p - stride
        if not grid[x]:
            if x == e:
                return str(nd)
            grid[x] = 1
            ap(x)
        x = p + stride
        if not grid[x]:
            if x == e:
                return str(nd)
            grid[x] = 1
            ap(x)


sys.stdout.write(solve() + "\n")

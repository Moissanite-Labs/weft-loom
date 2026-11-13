import sys

def solve(data):
    lines = data.split(b'\n')
    rows = []
    maxw = 0
    for l in lines:
        l = l.rstrip(b'\r')
        if l:
            rows.append(l)
            if len(l) > maxw:
                maxw = len(l)
    if not rows:
        return -1
    W = maxw + 2
    wall = b'#' * W
    parts = [wall]
    for r in rows:
        parts.append(b'#' + r + b'#' * (W - 1 - len(r)))
    parts.append(wall)
    flat = bytearray(b''.join(parts))
    s = flat.find(b'S')
    e = flat.find(b'E')
    if s < 0 or e < 0:
        return -1
    n = len(flat)
    visited = bytearray(n)
    queue = [0] * n
    visited[s] = 1
    queue[0] = s
    head = 0
    tail = 1
    dist = 0
    WALL = 35  # ord('#')
    while head < tail:
        level_end = tail
        while head < level_end:
            p = queue[head]
            head += 1
            if p == e:
                return dist
            q = p - 1
            if not visited[q] and flat[q] != WALL:
                visited[q] = 1
                queue[tail] = q
                tail += 1
            q = p + 1
            if not visited[q] and flat[q] != WALL:
                visited[q] = 1
                queue[tail] = q
                tail += 1
            q = p - W
            if not visited[q] and flat[q] != WALL:
                visited[q] = 1
                queue[tail] = q
                tail += 1
            q = p + W
            if not visited[q] and flat[q] != WALL:
                visited[q] = 1
                queue[tail] = q
                tail += 1
        dist += 1
    return -1

def main():
    data = sys.stdin.buffer.read()
    print(solve(data))

if __name__ == '__main__':
    main()

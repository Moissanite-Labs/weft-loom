import sys
from collections import deque

def solve(data: bytes) -> int:
    if not data:
        return -1
    if b'\r' in data:
        data = data.replace(b'\r\n', b'\n')
    data = data.strip(b'\n')
    if not data:
        return -1
    nl = data.find(b'\n')
    if nl == -1:
        W = len(data)
    else:
        W = nl

    stride = W + 1
    # Top wall of length stride (ends with '\n' so column W is always '\n' != '.')
    buf = bytearray(b'#' * W + b'\n')
    buf.extend(data)
    buf.extend(b'\n' + b'#' * W + b'\n')

    s_idx = buf.find(b'S')
    e_idx = buf.find(b'E')
    if s_idx == -1 or e_idx == -1:
        return -1
    if s_idx == e_idx:
        return 0

    DOT = 46
    WALL = 35
    buf[s_idx] = WALL
    buf[e_idx] = DOT

    q = deque([s_idx])
    popleft = q.popleft
    append = q.append
    qlen = q.__len__
    dist = 0

    while q:
        dist += 1
        for _ in range(qlen()):
            u = popleft()
            v = u - 1
            if buf[v] == DOT:
                if v == e_idx:
                    return dist
                buf[v] = WALL
                append(v)
            v = u + 1
            if buf[v] == DOT:
                if v == e_idx:
                    return dist
                buf[v] = WALL
                append(v)
            v = u - stride
            if buf[v] == DOT:
                if v == e_idx:
                    return dist
                buf[v] = WALL
                append(v)
            v = u + stride
            if buf[v] == DOT:
                if v == e_idx:
                    return dist
                buf[v] = WALL
                append(v)
    return -1

if __name__ == '__main__':
    print(solve(sys.stdin.buffer.read()))

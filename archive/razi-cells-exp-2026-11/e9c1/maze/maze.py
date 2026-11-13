import sys

def solve():
    data = sys.stdin.buffer.read()
    if not data:
        print(-1)
        return
    nl = data.find(b'\n')
    w = len(data) if nl == -1 else nl
    if w == 0:
        print(-1)
        return
    stride = w + 1
    buf = bytearray(data)
    if buf[-1] != 10:
        buf.append(10)
    # Translate '\n' (10) -> '#' (35)
    # Keep '.' (46), '#' (35), 'S' (83), 'E' (69)
    # Wait: faster than replace is translate or just leaving '\n' (10) as non-46!
    # Wait! In unidirectional or bidirectional BFS, we ONLY check if buf[v] == 46 (or target)!
    # '\n' is 10, '#' is 35. Neither is 46!
    # So we DO NOT EVEN NEED to replace '\n' with '#' if we only check `== 46`!
    # Wait: what about top/bottom out of bounds?
    # If we append `b'#' * stride` at the end of buf, then:
    # row 0 going up (`u - stride`) gives a negative index in `[-stride, -1]`, which indexes into the `b'#' * stride` at the end of `buf`!
    # row h-1 going down (`u + stride`) indexes into the `b'#' * stride` at the end of `buf`!
    # col 0 going left (`u - 1`) hits either `-1` (end of `buf`, which is `#`) or the `\n` (10) of previous row!
    # col w-1 going right (`u + 1`) hits `\n` (10) of current row!
    # NEITHER 10 NOR 35 is 46, 1, or 2!
    # So we don't need `.replace(b'\n', b'#')` or `.splitlines()` at all!
    buf.extend(b'#' * stride)
    
    s = buf.find(83)
    e = buf.find(69)
    if s == -1 or e == -1:
        print(-1)
        return
    if s == e:
        print(0)
        return
    
    buf[s] = 1
    buf[e] = 2
    
    qs = [s]
    qe = [e]
    dist = 0
    neg_stride = -stride
    
    while qs and qe:
        dist += 1
        if len(qs) <= len(qe):
            nq = []
            app = nq.append
            for u in qs:
                v = u - 1
                b = buf[v]
                if b == 46:
                    buf[v] = 1
                    app(v)
                elif b == 2:
                    print(dist)
                    return
                v = u + 1
                b = buf[v]
                if b == 46:
                    buf[v] = 1
                    app(v)
                elif b == 2:
                    print(dist)
                    return
                v = u + neg_stride
                b = buf[v]
                if b == 46:
                    buf[v] = 1
                    app(v)
                elif b == 2:
                    print(dist)
                    return
                v = u + stride
                b = buf[v]
                if b == 46:
                    buf[v] = 1
                    app(v)
                elif b == 2:
                    print(dist)
                    return
            qs = nq
        else:
            nq = []
            app = nq.append
            for u in qe:
                v = u - 1
                b = buf[v]
                if b == 46:
                    buf[v] = 2
                    app(v)
                elif b == 1:
                    print(dist)
                    return
                v = u + 1
                b = buf[v]
                if b == 46:
                    buf[v] = 2
                    app(v)
                elif b == 1:
                    print(dist)
                    return
                v = u + neg_stride
                b = buf[v]
                if b == 46:
                    buf[v] = 2
                    app(v)
                elif b == 1:
                    print(dist)
                    return
                v = u + stride
                b = buf[v]
                if b == 46:
                    buf[v] = 2
                    app(v)
                elif b == 1:
                    print(dist)
                    return
            qe = nq
    print(-1)

if __name__ == '__main__':
    solve()

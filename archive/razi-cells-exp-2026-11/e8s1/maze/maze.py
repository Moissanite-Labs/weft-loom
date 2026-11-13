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
    if nl == -1:
        W = len(data)
        stride = W + 1
        pad = b'#' * stride
        buf = bytearray(pad + data + b'#' + pad)
        start = s_pos + stride
        end = e_pos + stride
    elif nl > 0 and data[nl - 1] != 13 and len(data) % (nl + 1) <= 1:
        stride = nl + 1
        pad = b'#' * stride
        buf = bytearray(pad)
        buf.extend(data)
        if data[-1] != 10:
            buf.append(10)
        buf.extend(pad)
        start = s_pos + stride
        end = e_pos + stride
    else:
        lines = data.splitlines()
        while lines and not lines[-1]:
            lines.pop()
        W = len(lines[0])
        stride = W + 1
        pad = b'#' * stride
        buf = bytearray(pad + b'#'.join(lines) + b'#' + pad)
        start = buf.find(b'S')
        end = buf.find(b'E')

    buf[start] = 1
    buf[end] = 2

    qs = [start]
    qe = [end]
    dist = 0
    w1 = stride
    w_neg1 = -stride

    while qs and qe:
        dist += 1
        if len(qs) <= len(qe):
            nq = []
            app = nq.append
            for u in qs:
                c = buf[v := u + 1]
                if c == 46:
                    buf[v] = 1
                    app(v)
                elif c == 2:
                    print(dist)
                    return
                c = buf[v := u - 1]
                if c == 46:
                    buf[v] = 1
                    app(v)
                elif c == 2:
                    print(dist)
                    return
                c = buf[v := u + w1]
                if c == 46:
                    buf[v] = 1
                    app(v)
                elif c == 2:
                    print(dist)
                    return
                c = buf[v := u + w_neg1]
                if c == 46:
                    buf[v] = 1
                    app(v)
                elif c == 2:
                    print(dist)
                    return
            qs = nq
        else:
            nq = []
            app = nq.append
            for u in qe:
                c = buf[v := u + 1]
                if c == 46:
                    buf[v] = 2
                    app(v)
                elif c == 1:
                    print(dist)
                    return
                c = buf[v := u - 1]
                if c == 46:
                    buf[v] = 2
                    app(v)
                elif c == 1:
                    print(dist)
                    return
                c = buf[v := u + w1]
                if c == 46:
                    buf[v] = 2
                    app(v)
                elif c == 1:
                    print(dist)
                    return
                c = buf[v := u + w_neg1]
                if c == 46:
                    buf[v] = 2
                    app(v)
                elif c == 1:
                    print(dist)
                    return
            qe = nq

    print(-1)

if __name__ == '__main__':
    solve()

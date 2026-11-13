import sys
def main():
    data = sys.stdin.buffer.read()
    lines = data.split()
    if not lines:
        print(-1); return
    n = len(lines); w = max(map(len, lines)); W = w + 1
    if min(map(len, lines)) == w and len(data) in (n * W, n * W - 1) and not data[w::W].strip():
        g = bytearray(W) + data + bytearray(W)
    else:
        g = bytearray(W) + b'#'.join([l.ljust(w, b'#') for l in lines]) + bytearray(W)
    s = g.find(b'S'); e = g.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    dx = e % W - s % W; dy = e // W - s // W
    a = 1 if dx >= 0 else -1
    b = W if dy >= 0 else -W
    base = abs(dx) + abs(dy)
    g[e] = 46; g[s] = 47
    cur = [s]; k = 0
    while cur:
        stack = []
        push = stack.append
        for c in cur:
            if g[c] == 47:
                g[c] = 35; push(c)
        nxt = []
        app = nxt.append
        for c in stack:
            m = c + a
            if g[m] > 45:
                g[m] = 35; push(m)
            m = c + b
            if g[m] > 45:
                g[m] = 35; push(m)
            m = c - a
            if g[m] == 46:
                g[m] = 47; app(m)
            m = c - b
            if g[m] == 46:
                g[m] = 47; app(m)
        if g[e] == 35:
            print(base + 2 * k); return
        cur = nxt; k += 1
    print(-1)
main()

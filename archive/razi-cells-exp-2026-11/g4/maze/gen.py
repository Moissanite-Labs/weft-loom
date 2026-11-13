import random, sys

def gen(w, h, seed, loops=0):
    rnd = random.Random(seed)
    g = bytearray(b'#' * (w * h))
    cw = w // 2
    ch = h // 2
    vis = bytearray(cw * ch)
    stack = [0]
    vis[0] = 1
    g[1 * w + 1] = 46
    while stack:
        c = stack[-1]
        cx = c % cw
        cy = c // cw
        opts = []
        if cx > 0:
            nc = c - 1
            if not vis[nc]:
                opts.append((nc, 2*cx, 2*cy+1))
        if cx + 1 < cw:
            nc = c + 1
            if not vis[nc]:
                opts.append((nc, 2*cx+2, 2*cy+1))
        if cy > 0:
            nc = c - cw
            if not vis[nc]:
                opts.append((nc, 2*cx+1, 2*cy))
        if cy + 1 < ch:
            nc = c + cw
            if not vis[nc]:
                opts.append((nc, 2*cx+1, 2*cy+2))
        if not opts:
            stack.pop()
            continue
        nc, wx, wy = rnd.choice(opts)
        g[wy*w+wx] = 46
        ncx = 2*(nc % cw) + 1
        ncy = 2*(nc // cw) + 1
        g[ncy*w+ncx] = 46
        vis[nc] = 1
        stack.append(nc)
    for _ in range(loops):
        x = rnd.randrange(1, w-1)
        y = rnd.randrange(1, h-1)
        if g[y*w+x] == 35:
            g[y*w+x] = 46
    sx, sy = 1, 1
    ex, ey = 2*(cw-1)+1, 2*(ch-1)+1
    g[sy*w+sx] = 83
    g[ey*w+ex] = 69
    return g

if __name__ == '__main__':
    w = int(sys.argv[1]); h = int(sys.argv[2])
    seed = int(sys.argv[3]); out = sys.argv[4]
    g = gen(w, h, seed)
    with open(out, 'wb') as f:
        for y in range(h):
            f.write(g[y*w:(y+1)*w])
            f.write(b'\n')

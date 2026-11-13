import sys
def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        print(-1); return
    H = len(data); W = max(map(len, data)); w = W + 1
    flat = b''.join([r.ljust(w, b'#') for r in data])
    s = flat.find(b'S'); e = flat.find(b'E')
    if s < 0 or e < 0:
        print(-1); return
    si, sj = divmod(s, w); ei, ej = divmod(e, w)
    tb = bytearray(b'1' * 256); tb[35] = 48
    bits = flat.translate(bytes(tb))
    D = H + W
    free = []
    for d in range(D):
        i0 = d - W if d > W else 0
        i1 = d if d < H else H - 1
        free.append(int(bits[d + i0 * W: d + i1 * W + 1: W], 2) << (d - i1))
    free.append(0)
    ss = si + sj; es = ei + ej; eb = 1 << ej
    free[ss] ^= 1 << sj
    front = {ss: 1 << sj}
    d = 0
    while front:
        d += 1
        nf = {}
        for s, f in front.items():
            t = s + 1
            a = (f | f << 1) & free[t]
            if a:
                if t in nf: nf[t] |= a
                else: nf[t] = a
            t = s - 1
            a = (f | f >> 1) & free[t]
            if a:
                if t in nf: nf[t] |= a
                else: nf[t] = a
        for s, a in nf.items():
            free[s] ^= a
        if es in nf and nf[es] & eb:
            print(d); return
        front = nf
    print(-1)
main()

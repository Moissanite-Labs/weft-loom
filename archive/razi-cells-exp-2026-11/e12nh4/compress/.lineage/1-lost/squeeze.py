import lzma, bz2, zlib, math, struct
_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0, "dict_size": 1 << 20}]
_ST = [math.log((i + .5) / (4095.5 - i)) for i in range(4096)]
_M = (1 << 22) - 1

def _cm(data, n, enc):
    N = 5
    T = [[2048] * (1 << 22) for _ in range(N - 1)]
    W = [[0.3] * N for _ in range(256)]
    x1, x2, x = 0, 0xffffffff, 0
    out = bytearray()
    pos = 0
    if not enc:
        x = int.from_bytes(data[:4].ljust(4, b"\0"), "big"); pos = 4
    h = [0, 0, 0, 0]
    c1 = c2 = c3 = 0
    res = bytearray()
    ST = _ST; exp = math.exp
    for i in range(n):
        bases = (0, (c1 + 1) * 0x9E3779B1, (c1 | c2 << 8) * 0x85EBCA6B + 7, (c1 | c2 << 8 | c3 << 16) * 0xC2B2AE35 + 13)
        cur = data[i] if enc else 0
        c0 = 1
        for k in range(7, -1, -1):
            idx = [((b + c0 * 0x2545F491) >> 3 ^ b >> 15 ^ c0) & _M for b in bases]
            ps = [T[j][idx[j]] for j in range(4)]
            s = [ST[p] for p in ps]
            s.append(0.4)
            w = W[c0]
            dot = sum(a * b for a, b in zip(w, s))
            if dot > 20: dot = 20
            elif dot < -20: dot = -20
            pf = 1 / (1 + exp(-dot))
            p = int(pf * 4096)
            if p < 1: p = 1
            elif p > 4095: p = 4095
            xm = x1 + ((x2 - x1) >> 12) * p
            if enc:
                bit = (cur >> k) & 1
            else:
                bit = 1 if x <= xm else 0
            if bit: x2 = xm
            else: x1 = xm + 1
            err = (bit - pf) * 0.02
            for j in range(N):
                w[j] += err * s[j]
            for j in range(4):
                t = T[j]; q = t[idx[j]]
                t[idx[j]] = q + (((bit << 12) - q) >> 4 if j < 2 else ((bit << 12) - q) >> 3) if True else q
            while (x1 ^ x2) & 0xff000000 == 0:
                if enc: out.append(x2 >> 24)
                else:
                    x = ((x << 8) & 0xffffffff) | (data[pos] if pos < len(data) else 0); pos += 1
                x1 = (x1 << 8) & 0xffffffff
                x2 = ((x2 << 8) & 0xffffffff) | 255
            c0 = c0 * 2 + bit
        c3 = c2; c2 = c1; c1 = c0 & 255
        if not enc: res.append(c1)
    if enc:
        out += x1.to_bytes(4, "big")
        return bytes(out)
    return bytes(res)

def compress(b):
    c = [b"\0" + lzma.compress(b, format=lzma.FORMAT_RAW, filters=_F),
         b"\1" + bz2.compress(b, 9), b"\2" + zlib.compress(b, 9), b"\3" + b]
    if len(b) < 2000000:
        c.append(b"\4" + struct.pack(">I", len(b)) + _cm(b, len(b), True))
    return min(c, key=len)

def decompress(d):
    t, p = d[0], d[1:]
    if t == 0: return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=_F)
    if t == 1: return bz2.decompress(p)
    if t == 2: return zlib.decompress(p)
    if t == 4: return _cm(p[4:], struct.unpack(">I", p[:4])[0], False)
    return p

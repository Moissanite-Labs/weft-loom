import lzma, bz2, zlib, re
from itertools import accumulate
from bisect import bisect_right

_F = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME, "lc": 4, "lp": 0, "pb": 0,
       "nice_len": 273, "mf": lzma.MF_BT4, "depth": 0}]
_TOK = re.compile(rb"[A-Za-z]+| +|[^A-Za-z ]")
INC = 1
ORDERS = (1, 2, 3)
_M64 = (1 << 64) - 1
_TOP = 1 << 56
_M56 = (1 << 56) - 1
_LIMIT = 1 << 28


def _vw(n):
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n)
    return bytes(out)


def _vr(b, p):
    n = 0; sh = 0
    while True:
        x = b[p]; p += 1
        n |= (x & 0x7F) << sh; sh += 7
        if x < 0x80:
            return n, p


class _RC:
    def __init__(s):
        s.low = 0; s.rng = _M64; s.cache = 0; s.csize = 1; s.out = bytearray()

    def encode(s, cum, freq, tot):
        r = s.rng // tot
        s.low += r * cum
        s.rng = r * freq
        while s.rng < _TOP:
            s.rng <<= 8
            s._shift()

    def _shift(s):
        low = s.low
        if low < (0xFF << 56) or low > _M64:
            carry = low >> 64
            temp = s.cache
            while True:
                s.out.append((temp + carry) & 0xFF)
                temp = 0xFF
                s.csize -= 1
                if s.csize == 0:
                    break
            s.cache = (low >> 56) & 0xFF
        s.csize += 1
        s.low = (low & _M56) << 8

    def finish(s):
        for _ in range(9):
            s._shift()
        return bytes(s.out)


class _RD:
    def __init__(s, data, pos):
        s.data = data + b"\0" * 16; s.pos = pos + 9; s.rng = _M64
        code = 0
        for b in data[pos:pos + 9]:
            code = (code << 8) | b
        s.code = code; s.r = 1

    def get(s, tot):
        s.r = s.rng // tot
        v = s.code // s.r
        return v if v < tot else tot - 1

    def consume(s, cum, freq):
        s.code -= s.r * cum
        s.rng = s.r * freq
        while s.rng < _TOP:
            s.rng <<= 8
            s.code = (s.code << 8) | s.data[s.pos]; s.pos += 1


def _upd(touched, s):
    for c in touched:
        syms, cnts, idx, tot = c
        i = idx.get(s)
        if i is None:
            idx[s] = len(syms); syms.append(s); cnts.append(INC)
        else:
            cnts[i] += INC
        tot += INC
        if tot + len(syms) > _LIMIT:
            cnts = [(x + 1) >> 1 for x in cnts]; c[1] = cnts; tot = sum(cnts)
        c[3] = tot


def _ppm_encode(ids, V, order):
    rc = _RC(); D = {}
    hist = (-1,) * order
    for s in ids:
        k = order; coded = False; touched = []
        while k >= 0:
            key = hist[order - k:]
            c = D.get(key)
            if c is None:
                c = [[], [], {}, 0]; D[key] = c
            touched.append(c)
            syms, cnts, idx, tot = c
            n = len(syms)
            if n:
                i = idx.get(s)
                T = tot + n
                if i is not None:
                    rc.encode(sum(cnts[:i]), cnts[i], T)
                    coded = True
                    break
                rc.encode(tot, n, T)
            k -= 1
        if not coded:
            rc.encode(s, 1, V)
        _upd(touched, s)
        if order:
            hist = hist[1:] + (s,)
    return rc.finish()


def _ppm_decode(data, pos, ntok, V, order):
    rd = _RD(data, pos); D = {}
    hist = (-1,) * order
    out = []
    for _ in range(ntok):
        k = order; coded = False; touched = []
        while k >= 0:
            key = hist[order - k:]
            c = D.get(key)
            if c is None:
                c = [[], [], {}, 0]; D[key] = c
            touched.append(c)
            syms, cnts, idx, tot = c
            n = len(syms)
            if n:
                T = tot + n
                v = rd.get(T)
                if v >= tot:
                    rd.consume(tot, n)
                else:
                    cum = list(accumulate(cnts))
                    i = bisect_right(cum, v)
                    rd.consume(cum[i] - cnts[i], cnts[i])
                    s = syms[i]; coded = True
                    break
            k -= 1
        if not coded:
            s = rd.get(V); rd.consume(s, 1)
        _upd(touched, s)
        out.append(s)
        if order:
            hist = hist[1:] + (s,)
    return out


def _ppm_compress(data):
    toks = _TOK.findall(data)
    if not toks:
        return None
    vocab = sorted(set(toks))
    vidx = {t: i for i, t in enumerate(vocab)}
    ids = [vidx[t] for t in toks]
    V = len(vocab)
    vb = b"".join(_vw(len(t)) + t for t in vocab)
    vc = lzma.compress(vb, format=lzma.FORMAT_RAW, filters=_F)
    sample = ids[:30000] if len(ids) > 60000 else ids
    best = min(ORDERS, key=lambda o: len(_ppm_encode(sample, V, o)))
    body = _ppm_encode(ids, V, best) if sample is not ids else None
    if body is None:
        body = _ppm_encode(ids, V, best)
    return bytes([best]) + _vw(len(ids)) + _vw(V) + _vw(len(vc)) + vc + body


def _ppm_decompress(blob):
    order = blob[0]
    ntok, p = _vr(blob, 1)
    V, p = _vr(blob, p)
    lvc, p = _vr(blob, p)
    vb = lzma.decompress(blob[p:p + lvc], format=lzma.FORMAT_RAW, filters=_F)
    p += lvc
    vocab = []; q = 0
    for _ in range(V):
        L, q = _vr(vb, q); vocab.append(vb[q:q + L]); q += L
    ids = _ppm_decode(blob, p, ntok, V, order)
    return b"".join([vocab[i] for i in ids])


def _cands(data):
    yield b"\x00" + lzma.compress(data, format=lzma.FORMAT_RAW, filters=_F)
    yield b"\x01" + bz2.compress(data, 9)
    yield b"\x02" + zlib.compress(data, 9)
    yield b"\x03" + data
    t = _ppm_compress(data)
    if t is not None:
        yield b"\x05" + t


def compress(data: bytes) -> bytes:
    return min(_cands(data), key=len)


def decompress(blob: bytes) -> bytes:
    t, body = blob[0], blob[1:]
    if t == 0:
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_F)
    if t == 1:
        return bz2.decompress(body)
    if t == 2:
        return zlib.decompress(body)
    if t == 5:
        return _ppm_decompress(body)
    return body

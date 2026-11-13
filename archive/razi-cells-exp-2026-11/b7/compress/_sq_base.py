"""squeeze.py - stdlib-only exact round-trip compressor.

compress(bytes) -> bytes, decompress(bytes) -> bytes.
Wire format: first byte is a method id; the rest is that method's payload.
compress() evaluates every registered method and keeps the smallest output.
Every method is exactly reversible for arbitrary byte strings.
"""
import bz2, heapq, lzma, re, zlib

# ---------------------------------------------------------------- utilities
def _vi(n, out):
    """append unsigned LEB128 varint n to bytearray out"""
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80)
        n >>= 7
    out.append(n)


def _rvi(b, p):
    """read unsigned LEB128 at position p; return (value, newpos)"""
    n = 0
    s = 0
    while True:
        c = b[p]
        p += 1
        n |= (c & 0x7F) << s
        if c < 0x80:
            return n, p
        s += 7


# ------------------------------------------- reversible phrase substitution
# Marker byte 0x00 introduces a code.  0x00 0x00 is a literal NUL.
# 0x00 c (c>=1) is dictionary phrase c-1.  Literal bytes != 0 pass through.
_WORD = re.compile(rb"[A-Za-z0-9_]+")


def _mine(d, maxcodes=250):
    """Learn the most valuable repeated substrings from d itself."""
    spans = [m.span() for m in _WORD.finditer(d)]
    n = len(spans)
    cnt = {}
    for k in (1, 2, 3, 4):
        for i in range(n - k + 1):
            a = spans[i][0]
            z = spans[i + k - 1][1]
            p = d[a:z]
            if len(p) >= 4:
                cnt[p] = cnt.get(p, 0) + 1
            if i:
                a2 = spans[i - 1][1]
                if a2 < z:
                    q = d[a2:z]
                    if len(q) >= 4:
                        cnt[q] = cnt.get(q, 0) + 1
    gen = ((c * (len(p) - 3), p) for p, c in cnt.items() if c >= 3)
    best = heapq.nlargest(maxcodes, gen, key=lambda x: (x[0], len(x[1]), x[1]))
    return [p for _, p in best]


def _tok_encode(d):
    phrases = _mine(d)
    table = {}
    for idx, p in enumerate(phrases):
        table.setdefault(p[:4], []).append((p, idx + 1))
    for cands in table.values():
        cands.sort(key=lambda x: -len(x[0]))
    out = bytearray()
    _vi(len(phrases), out)
    for p in phrases:
        _vi(len(p), out)
        out += p
    i = 0
    N = len(d)
    while i < N:
        cands = table.get(d[i:i + 4])
        hit = False
        if cands:
            for p, code in cands:
                if d.startswith(p, i):
                    out.append(0)
                    out.append(code)
                    i += len(p)
                    hit = True
                    break
        if not hit:
            b = d[i]
            if b == 0:
                out.append(0)
                out.append(0)
            else:
                out.append(b)
            i += 1
    return bytes(out)


def _tok_decode(b):
    p = 0
    n, p = _rvi(b, p)
    phrases = []
    for _ in range(n):
        L, p = _rvi(b, p)
        phrases.append(b[p:p + L])
        p += L
    out = bytearray()
    N = len(b)
    while p < N:
        c = b[p]
        p += 1
        if c == 0:
            if p >= N:
                break
            k = b[p]
            p += 1
            if k == 0:
                out.append(0)
            else:
                out += phrases[k - 1]
        else:
            out.append(c)
    return bytes(out)


# ------------------------------------------------------------- raw lzma1
def _lzraw(d, lc, lp, pb):
    f = [{"id": lzma.FILTER_LZMA1, "dict_size": 1 << 23,
          "lc": lc, "lp": lp, "pb": pb}]
    return lzma.compress(d, format=lzma.FORMAT_RAW, filters=f)


def _unlzraw(b, lc, lp, pb):
    f = [{"id": lzma.FILTER_LZMA1, "dict_size": 1 << 23,
          "lc": lc, "lp": lp, "pb": pb}]
    return lzma.decompress(b, format=lzma.FORMAT_RAW, filters=f)


# ------------------------------------------------------------- method table
def _id(d):
    return d


def _z(d):
    return zlib.compress(d, 9)


def _bz(d):
    return bz2.compress(d, 9)


def _lz9(d):
    return lzma.compress(d, preset=9)


def _lz6(d):
    return lzma.compress(d, preset=6)


def _t_bz(d):
    return bz2.compress(_tok_encode(d), 9)


def _t_z(d):
    return zlib.compress(_tok_encode(d), 9)


def _t_lz(d):
    return lzma.compress(_tok_encode(d), preset=6)


def _t_lzr(d):
    return _lzraw(_tok_encode(d), 4, 0, 2)


def _t2_bz(d):
    return bz2.compress(_tok_encode(_tok_encode(d)), 9)


_ENCODERS = [
    _id, _z, _bz, _lz9, _lz6,
    lambda d: _lzraw(d, 4, 0, 2),
    lambda d: _lzraw(d, 3, 1, 2),
    _t_bz, _t_z, _t_lz, _t_lzr, _t2_bz,
]

_DECODERS = [
    _id,
    zlib.decompress,
    bz2.decompress,
    lzma.decompress,
    lzma.decompress,
    lambda b: _unlzraw(b, 4, 0, 2),
    lambda b: _unlzraw(b, 3, 1, 2),
    lambda b: _tok_decode(bz2.decompress(b)),
    lambda b: _tok_decode(zlib.decompress(b)),
    lambda b: _tok_decode(lzma.decompress(b)),
    lambda b: _tok_decode(_unlzraw(b, 4, 0, 2)),
    lambda b: _tok_decode(_tok_decode(bz2.decompress(b))),
]


def compress(data):
    data = bytes(data)
    best = None
    best_id = 0
    for mid, enc in enumerate(_ENCODERS):
        try:
            payload = enc(data)
        except Exception:
            continue
        if best is None or len(payload) < len(best):
            best = payload
            best_id = mid
    return bytes([best_id]) + best


def decompress(blob):
    blob = bytes(blob)
    if not blob:
        return b""
    return _DECODERS[blob[0]](blob[1:])

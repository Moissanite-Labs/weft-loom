"""squeeze: stdlib-only compressor.

Picks the smallest of: stored / LZMA variants / bz2 / deflate / Huffman-only deflate (tags 0..0x12),
a word-token transform for ASCII data (tag 0x20: dictionary of frequent words and separators learned
from the input, implied single spaces, capital flags, then each stream packed with the best codec),
and a two-halves split (tag 0x30) for inputs whose halves differ in nature.
"""
import lzma, bz2, zlib, re
from collections import Counter

_X = 9 | lzma.PRESET_EXTREME
_LZ_FILTERS = [
    [{"id": lzma.FILTER_LZMA2, "preset": _X}],
    [{"id": lzma.FILTER_LZMA2, "preset": _X, "lc": 4, "lp": 0, "pb": 0}],
    [{"id": lzma.FILTER_LZMA2, "preset": _X, "lc": 3, "lp": 0, "pb": 0}],
    [{"id": lzma.FILTER_LZMA2, "preset": _X, "lc": 0, "lp": 0, "pb": 0}],
]
_ATOM = re.compile(rb"[A-Za-z0-9]+|[^A-Za-z0-9]+")
_LOWER = re.compile(rb"[a-z]+\Z")
_CAPW = re.compile(rb"[A-Z][a-z]*\Z")
_ALPHA = re.compile(rb"[A-Za-z]+\Z")
_ALNUM = frozenset(b"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
_ONE = [bytes((i,)) for i in range(256)]


def _vi(n):
    out = bytearray()
    while n >= 128:
        out.append(n & 127 | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def _rvi(b, i):
    n = s = 0
    while True:
        c = b[i]
        i += 1
        n |= (c & 127) << s
        s += 7
        if c < 128:
            return n, i


def _plain(data):
    best = b"\x00" + data
    for i, f in enumerate(_LZ_FILTERS):
        c = bytes([1 + i]) + lzma.compress(data, format=lzma.FORMAT_RAW, filters=f)
        if len(c) < len(best):
            best = c
    c = b"\x10" + bz2.compress(data, 9)
    if len(c) < len(best):
        best = c
    co = zlib.compressobj(9, zlib.DEFLATED, -15)
    c = b"\x11" + co.compress(data) + co.flush()
    if len(c) < len(best):
        best = c
    co = zlib.compressobj(9, zlib.DEFLATED, -15, 9, zlib.Z_HUFFMAN_ONLY)
    c = b"\x12" + co.compress(data) + co.flush()
    if len(c) < len(best):
        best = c
    return best


def _unplain(blob):
    tag, body = blob[0], blob[1:]
    if tag == 0:
        return body
    if 1 <= tag <= len(_LZ_FILTERS):
        return lzma.decompress(body, format=lzma.FORMAT_RAW, filters=_LZ_FILTERS[tag - 1])
    if tag == 0x10:
        return bz2.decompress(body)
    if tag == 0x11 or tag == 0x12:
        return zlib.decompress(body, -15)
    raise ValueError("bad tag")


def _key(a):
    if _LOWER.match(a):
        return a, False
    if _CAPW.match(a):
        return a.lower(), True
    if _ALPHA.match(a):
        return a, False
    return None


def _wt(data):
    """Word-token transform. data must be non-empty pure ASCII."""
    atoms = _ATOM.findall(data)
    n = len(atoms)
    par = 0 if atoms[0][0] in _ALNUM else 1
    cache = {}
    keys = [None] * n
    wc = Counter()
    for i in range(par, n, 2):
        a = atoms[i]
        k = cache.get(a, 0)
        if k == 0:
            k = cache[a] = _key(a)
        if k is not None:
            keys[i] = k
            wc[k[0]] += 1
    words = {w for w, c in wc.most_common(12000) if c >= 2}
    for i in range(par, n, 2):
        k = keys[i]
        if k is not None and k[0] not in words:
            keys[i] = None
    sc = Counter()
    items = [None] * n
    last = n - 1
    for i in range(1 - par, n, 2):
        a = atoms[i]
        p = keys[i - 1] if i > 0 else None
        nx = keys[i + 1] if i < last else None
        cap = nx is not None and nx[1]
        if a == b" " and not cap and 0 < i < last and (p is not None or nx is not None):
            continue
        t = (a, cap)
        sc[t] += 1
        items[i] = t
    seps = {t for t, c in sc.most_common(4000) if c >= 2}
    capn = sum(c for t, c in sc.items() if t[1] and t not in seps)
    toks = [(-wc[w], 0, w) for w in words]
    toks += [(-sc[t], 2 if t[1] else 1, t[0]) for t in seps]
    toks.append((-capn, 3, b""))
    toks.sort()
    V = len(toks)
    E = 0 if V <= 128 else -(-(V - 128) // 255)
    D = 128 - E
    wcode = {}
    scode = {}
    capcode = None
    for r, (_, kind, s) in enumerate(toks):
        if r < D:
            code = (128 + r, -1)
        else:
            q = r - D
            code = (128 + D + q % E, q // E)
        if kind == 0:
            wcode[s] = code
        elif kind == 3:
            capcode = code
        else:
            scode[(s, kind == 2)] = code
    A = bytearray()
    B = bytearray()
    for i, a in enumerate(atoms):
        if (i & 1) == par:
            k = keys[i]
            if k is None:
                A += a
                continue
            if i == 0 and k[1]:
                A.append(capcode[0])
                if capcode[1] >= 0:
                    B.append(capcode[1])
            code = wcode[k[0]]
        else:
            t = items[i]
            if t is None:
                continue
            code = scode.get(t)
            if code is None:
                A += a
                if not t[1]:
                    continue
                code = capcode
        A.append(code[0])
        if code[1] >= 0:
            B.append(code[1])
    d = _vi(V) + bytes(t[1] for t in toks) + b"".join(_vi(len(t[2])) for t in toks) + b"".join(t[2] for t in toks)
    out = [b"\x20"]
    for s in (d, bytes(A), bytes(B)):
        p = _plain(s)
        out.append(_vi(len(p)))
        out.append(p)
    return b"".join(out)


def _unwt(blob):
    i = 1
    secs = []
    for _ in range(3):
        ln, i = _rvi(blob, i)
        secs.append(_unplain(blob[i:i + ln]))
        i += ln
    d, A, B = secs
    V, j = _rvi(d, 0)
    kinds = d[j:j + V]
    j += V
    lens = []
    for _ in range(V):
        ln, j = _rvi(d, j)
        lens.append(ln)
    toks = []
    for ln in lens:
        toks.append(d[j:j + ln])
        j += ln
    E = 0 if V <= 128 else -(-(V - 128) // 255)
    D = 128 - E
    out = []
    prev = 0  # 1 word token, 2 raw alnum byte, 3 separator
    pc = False
    bi = 0
    for b in A:
        if b < 128:
            if b in _ALNUM:
                if prev == 1:
                    out.append(b" ")
                prev = 2
            else:
                prev = 3
            out.append(_ONE[b])
            continue
        r = b - 128
        if r >= D:
            r = D + B[bi] * E + (r - D)
            bi += 1
        k = kinds[r]
        if k == 0:
            if prev == 1 or prev == 2:
                out.append(b" ")
            w = toks[r]
            if pc:
                w = w[:1].upper() + w[1:]
                pc = False
            out.append(w)
            prev = 1
        elif k == 3:
            pc = True
        else:
            out.append(toks[r])
            prev = 3
            if k == 2:
                pc = True
    return b"".join(out)


def _one(data):
    best = _plain(data)
    if len(data) >= 64 and data.isascii():
        c = _wt(data)
        if len(c) < len(best):
            best = c
    return best


def compress(data: bytes) -> bytes:
    data = bytes(data)
    best = _one(data)
    n = len(data)
    if n >= 8192:
        h = n // 2
        c1 = _one(data[:h])
        c = b"\x30" + _vi(len(c1)) + c1 + _one(data[h:])
        if len(c) < len(best):
            best = c
    return best


def decompress(blob: bytes) -> bytes:
    blob = bytes(blob)
    if not blob:
        raise ValueError("empty input")
    tag = blob[0]
    if tag == 0x20:
        return _unwt(blob)
    if tag == 0x30:
        ln, i = _rvi(blob, 1)
        return decompress(blob[i:i + ln]) + decompress(blob[i + ln:])
    return _unplain(blob)

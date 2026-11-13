import bz2, lzma, re

_LZMA_CFGS = [dict(lc=3, lp=0, pb=2), dict(lc=2, lp=0, pb=0)]
def _filters(cfg):
    f = dict(id=lzma.FILTER_LZMA1, dict_size=1 << 23, mode=lzma.MODE_NORMAL,
             nice_len=273, mf=lzma.MF_BT4, depth=0)
    f.update(cfg); return [f]
_DEC = [_filters(c) for c in _LZMA_CFGS]
_M_BZ2 = 200
_M_STORE = 201

def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7f; n >>= 7
        if n: out.append(b | 0x80)
        else:
            out.append(b); return bytes(out)

def _readvarint(buf, i):
    n = 0; s = 0
    while True:
        b = buf[i]; i += 1
        n |= (b & 0x7f) << s
        if not b & 0x80: return n, i
        s += 7

def _pack(b):
    best = bytes([_M_STORE]) + b
    n = len(best)
    for i, flt in enumerate(_DEC):
        c = lzma.compress(b, format=lzma.FORMAT_RAW, filters=flt)
        if len(c) + 1 < n:
            best = bytes([i]) + c; n = len(best)
    if len(b) > 32:
        c = bz2.compress(b, 9)
        if len(c) + 1 < n:
            best = bytes([_M_BZ2]) + c; n = len(best)
    return best

def _unpack(blob):
    m = blob[0]; p = blob[1:]
    if m == _M_STORE: return p
    if m == _M_BZ2: return bz2.decompress(p)
    return lzma.decompress(p, format=lzma.FORMAT_RAW, filters=_DEC[m])

_WORD = re.compile(rb"[A-Za-z]+")

def _split(data):
    words = []; gaps = []; pos = 0
    for m in _WORD.finditer(data):
        gaps.append(data[pos:m.start()]); words.append(m.group()); pos = m.end()
    gaps.append(data[pos:])
    return words, gaps

def compress(data):
    data = bytes(data)
    best = b"\x01" + _pack(data)
    words, gaps = _split(data)
    if len(words) >= 8:
        W = b"".join(words)
        meta = bytearray()
        for k in range(len(gaps)):
            g = gaps[k]
            meta += _varint(len(g)); meta += g
            if k < len(words): meta += _varint(len(words[k]))
        wblob = _pack(W); mblob = _pack(bytes(meta))
        out = b"\x03" + _varint(len(wblob)) + wblob + mblob
        if len(out) < len(best): best = out
    return best

def decompress(blob):
    blob = bytes(blob)
    if not blob: return b""
    t = blob[0]
    if t == 1: return _unpack(blob[1:])
    if t != 3: raise ValueError("bad type")
    i = 1
    wl, i = _readvarint(blob, i)
    W = _unpack(blob[i:i+wl])
    M = _unpack(blob[i+wl:])
    out = bytearray(); j = 0; k = 0; nM = len(M); nW = len(W)
    while j < nM:
        n, j = _readvarint(M, j)
        out += M[j:j+n]; j += n
        if j < nM:
            n2, j = _readvarint(M, j)
            out += W[k:k+n2]; k += n2
    return bytes(out)

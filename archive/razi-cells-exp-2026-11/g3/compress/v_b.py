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
_MAX_DICT = 240

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
        freq = {}
        for w in words: freq[w] = freq.get(w, 0) + 1
        ranked = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:_MAX_DICT]
        dic = sorted(w for w, c in ranked)
        idx = {w: i for i, w in enumerate(dic)}
        esc = len(dic)
        wb = bytearray()
        for w in words:
            i = idx.get(w)
            if i is None:
                wb.append(esc); wb += _varint(len(w)); wb += w
            else:
                wb.append(i)
        gb = bytearray()
        for g in gaps:
            gb += _varint(len(g)); gb += g
        dblob = _pack(b"\n".join(dic))
        wblob = _pack(bytes(wb)); gblob = _pack(bytes(gb))
        out = b"\x02" + _varint(esc) + _varint(len(dblob)) + dblob + _varint(len(wblob)) + wblob + gblob
        if len(out) < len(best): best = out
    return best

def decompress(blob):
    blob = bytes(blob)
    if not blob: return b""
    t = blob[0]
    if t == 1: return _unpack(blob[1:])
    if t != 2: raise ValueError("bad type")
    i = 1
    ndict, i = _readvarint(blob, i)
    dl, i = _readvarint(blob, i)
    dic = blob[i:i+dl].split(b"\n") if ndict else []
    i += dl
    wl, i = _readvarint(blob, i)
    wb = _unpack(blob[i:i+wl])
    gb = _unpack(blob[i+wl:])
    words = []; j = 0; nw = len(wb)
    while j < nw:
        c = wb[j]; j += 1
        if c == ndict:
            n, j = _readvarint(wb, j)
            words.append(wb[j:j+n]); j += n
        else:
            words.append(dic[c])
    gaps = []; j = 0; ng = len(gb)
    while j < ng:
        n, j = _readvarint(gb, j)
        gaps.append(gb[j:j+n]); j += n
    out = bytearray()
    for k, w in enumerate(words):
        out += gaps[k]; out += w
    out += gaps[len(words)]
    return bytes(out)

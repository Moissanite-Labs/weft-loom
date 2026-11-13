"""squeeze: stdlib-only compressor. compress(bytes)->bytes, decompress(bytes)->bytes.
Word-tokenizing front end (dictionary + id stream + literal stream), each stream
coded with the best of raw/lzma/bz2/zlib; falls back to plain best codec."""
import lzma, bz2, zlib, re
from collections import Counter

_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME,
             "lc": 4, "lp": 0, "pb": 0, "nice_len": 273, "mf": lzma.MF_BT4, "depth": 0}]

_CODECS = {
    0: (lambda d: d, lambda d: d),
    1: (lambda d: lzma.compress(d, format=lzma.FORMAT_RAW, filters=_FILTERS),
        lambda d: lzma.decompress(d, format=lzma.FORMAT_RAW, filters=_FILTERS)),
    2: (lambda d: bz2.compress(d, 9), bz2.decompress),
    3: (lambda d: zlib.compress(d, 9), zlib.decompress),
}

def _best(data):
    best = bytes([0]) + data
    for cid, (c, _) in _CODECS.items():
        if cid == 0:
            continue
        try:
            out = c(data)
        except Exception:
            continue
        if len(out) + 1 < len(best):
            best = bytes([cid]) + out
    return best

def _undo(blob):
    return _CODECS[blob[0]][1](blob[1:])

def _varint(n):
    out = bytearray()
    while n >= 0x80:
        out.append((n & 0x7F) | 0x80); n >>= 7
    out.append(n)
    return bytes(out)

def _rvarint(buf, pos):
    n = 0; s = 0
    while True:
        b = buf[pos]; pos += 1
        n |= (b & 0x7F) << s
        if b < 0x80:
            return n, pos
        s += 7

_TOK = re.compile(rb'[A-Za-z]+|[^A-Za-z]+')

def _tokenize(data):
    toks = _TOK.findall(data)
    cnt = Counter()
    for t in toks:
        if t[0] < 128 and t.isalpha():
            lo = t.lower()
            if t == lo or t == lo[:1].upper() + lo[1:]:
                cnt[lo] += 1
    words = [w for w, c in cnt.most_common(65535) if c >= 2 and len(w) >= 2]
    words.sort(key=lambda w: (-cnt[w], w))
    idx = {w: i for i, w in enumerate(words)}
    wide = len(words) > 256
    lit = bytearray(); ids = bytearray()
    for t in toks:
        i = None
        if t[0] < 128 and t.isalpha():
            lo = t.lower()
            i = idx.get(lo)
            if i is not None:
                if t == lo:
                    lit.append(1)
                elif t == lo[:1].upper() + lo[1:]:
                    lit.append(2)
                else:
                    i = None
        if i is None:
            for b in t:
                if b <= 3:
                    lit.append(3)
                lit.append(b)
        else:
            if wide:
                ids.append(i >> 8)
            ids.append(i & 255)
    return b'\n'.join(words), bytes(lit), bytes(ids), wide

def _tok_compress(data):
    dwords, lit, ids, wide = _tokenize(data)
    parts = [_best(dwords), _best(lit), _best(ids)]
    out = bytearray([4 | (8 if wide else 0)])
    for p in parts:
        out += _varint(len(p)); out += p
    return bytes(out)

def _tok_decompress(data):
    wide = bool(data[0] & 8)
    pos = 1; parts = []
    for _ in range(3):
        n, pos = _rvarint(data, pos)
        parts.append(_undo(data[pos:pos + n])); pos += n
    dwords, lit, ids = parts
    words = dwords.split(b'\n') if dwords else []
    caps = [w[:1].upper() + w[1:] for w in words]
    out = bytearray(); j = 0; k = 0; n = len(lit)
    while k < n:
        b = lit[k]; k += 1
        if b > 3:
            out.append(b)
        elif b == 3:
            out.append(lit[k]); k += 1
        else:
            if wide:
                i = (ids[j] << 8) | ids[j + 1]; j += 2
            else:
                i = ids[j]; j += 1
            out += words[i] if b == 1 else caps[i]
    return bytes(out)

def compress(data: bytes) -> bytes:
    best = _best(data)
    try:
        t = _tok_compress(data)
        if len(t) < len(best) and _tok_decompress(t) == data:
            best = t
    except Exception:
        pass
    return best

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    if data[0] & 4:
        return _tok_decompress(data)
    return _undo(data)

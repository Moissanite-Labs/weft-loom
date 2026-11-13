import lzma, zlib, bz2, re, struct
from collections import Counter

_LZMA_FILTERS = [{"id": lzma.FILTER_LZMA2, "preset": 9 | lzma.PRESET_EXTREME,
                  "lc": 4, "lp": 0, "pb": 0, "nice_len": 273, "mf": lzma.MF_BT4, "depth": 0}]
_TOK = re.compile(rb"[A-Za-z]+ ?|[^A-Za-z]")
_ESC = 0xFF
_N1 = 0x40           # 1-byte codes 0x80..0xBF
_P2 = list(range(0xC0, 0xFF))  # 2-byte prefixes


def _lz(d):
    return lzma.compress(d, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)


def _unlz(d):
    return lzma.decompress(d, format=lzma.FORMAT_RAW, filters=_LZMA_FILTERS)


def _dict_encode(data):
    toks = _TOK.findall(data)
    cnt = Counter(t for t in toks if t[:1].isalpha() and len(t) >= 2)
    ranked = sorted(((c * (len(w) - 1), w) for w, c in cnt.items() if c >= 2 and c * (len(w) - 1) > len(w) + 2),
                    key=lambda x: (-x[0], x[1]))
    ranked = [w for _, w in ranked[:_N1 + len(_P2) * 256]]
    codes = {}
    for i, w in enumerate(ranked):
        if i < _N1:
            codes[w] = bytes([0x80 + i])
        else:
            j = i - _N1
            codes[w] = bytes([_P2[j >> 8], j & 0xFF])
    out = bytearray()
    for t in toks:
        c = codes.get(t)
        if c is not None:
            out += c
        else:
            for b in t:
                if b >= 0x80:
                    out.append(_ESC)
                out.append(b)
    dblob = _lz(b"\n".join(ranked))
    return struct.pack("<I", len(dblob)) + dblob + _lz(bytes(out))


def _dict_decode(body):
    (n,) = struct.unpack("<I", body[:4])
    words = _unlz(body[4:4 + n]).split(b"\n") if n > 0 else []
    s = _unlz(body[4 + n:])
    out = bytearray()
    i, L = 0, len(s)
    while i < L:
        b = s[i]
        if b < 0x80:
            out.append(b); i += 1
        elif b == _ESC:
            out.append(s[i + 1]); i += 2
        elif b < 0xC0:
            out += words[b - 0x80]; i += 1
        else:
            out += words[_N1 + ((b - 0xC0) << 8) + s[i + 1]]; i += 2
    return bytes(out)


def compress(data: bytes) -> bytes:
    cands = []
    try:
        cands.append(b"\x01" + _lz(data))
    except Exception:
        pass
    try:
        cands.append(b"\x04" + _dict_encode(data))
    except Exception:
        pass
    cands.append(b"\x02" + bz2.compress(data, 9))
    cands.append(b"\x03" + zlib.compress(data, 9))
    cands.append(b"\x00" + data)
    return min(cands, key=len)


def decompress(blob: bytes) -> bytes:
    tag, body = blob[:1], blob[1:]
    if tag == b"\x01":
        return _unlz(body)
    if tag == b"\x04":
        return _dict_decode(body)
    if tag == b"\x02":
        return bz2.decompress(body)
    if tag == b"\x03":
        return zlib.decompress(body)
    return body

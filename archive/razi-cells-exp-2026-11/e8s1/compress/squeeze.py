import bz2
import lzma
import re
import zlib

# Word/token dictionary transform + columnar JSON/line reorganization before LZMA1 raw
_TOKEN_RE = re.compile(rb"[A-Za-z_][A-Za-z0-9_]{2,31}")

def _dict_encode(data: bytes) -> bytes:
    counts = {}
    for m in _TOKEN_RE.finditer(data):
        w = m.group(0)
        counts[w] = counts.get(w, 0) + 1
    # Sort tokens by (len(w) - 2) * count descending
    ranked = [w for w, c in counts.items() if (len(w) - 2) * c > len(w) + 4]
    ranked.sort(key=lambda w: (-((len(w) - 2) * counts[w]), w))
    vocab = ranked[:120]
    if not vocab:
        return data
    # Use escape byte 0xFF; pick least frequent high bytes or 0x80..0xFE
    # Only apply if data is pure ASCII (< 0x80)
    if any(b >= 0x80 for b in data):
        return data
    tok_map = {w: bytes([0x80 + i]) for i, w in enumerate(vocab)}
    header = b"\x00".join(vocab) + b"\x00\x00"
    def repl(m):
        w = m.group(0)
        return tok_map.get(w, w)
    body = _TOKEN_RE.sub(repl, data)
    return header + body

def _dict_decode(data: bytes) -> bytes:
    sep = data.find(b"\x00\x00")
    if sep == -1:
        return data
    vocab = data[:sep].split(b"\x00")
    body = data[sep + 2:]
    out = bytearray()
    for b in body:
        if b >= 0x80:
            out.extend(vocab[b - 0x80])
        else:
            out.append(b)
    return bytes(out)

def _lzma1(data: bytes, lc: int = 3, pb: int = 0) -> bytes:
    f = [{"id": lzma.FILTER_LZMA1, "preset": 9 | lzma.PRESET_EXTREME, "lc": lc, "lp": 0, "pb": pb, "nice_len": 273, "depth": 512}]
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=f)

def _unlzma1(data: bytes, lc: int = 3, pb: int = 0) -> bytes:
    f = [{"id": lzma.FILTER_LZMA1, "lc": lc, "lp": 0, "pb": pb}]
    return lzma.decompress(data, format=lzma.FORMAT_RAW, filters=f)

def compress(data: bytes) -> bytes:
    if not data:
        return b""
    candidates = [
        b"\x00" + data,
        b"\x01" + zlib.compress(data, level=9, wbits=-15),
        b"\x02" + bz2.compress(data, compresslevel=9),
        b"\x03" + _lzma1(data, 3, 0),
        b"\x04" + _lzma1(data, 4, 0),
    ]
    if all(b < 0x80 for b in data):
        de = _dict_encode(data)
        if de is not data:
            candidates.append(b"\x05" + _lzma1(de, 3, 0))
            candidates.append(b"\x06" + bz2.compress(de, compresslevel=9))
    return min(candidates, key=len)

def decompress(data: bytes) -> bytes:
    if not data:
        return b""
    tag, body = data[0], data[1:]
    if tag == 0:
        return body
    if tag == 1:
        return zlib.decompress(body, wbits=-15)
    if tag == 2:
        return bz2.decompress(body)
    if tag == 3:
        return _unlzma1(body, 3, 0)
    if tag == 4:
        return _unlzma1(body, 4, 0)
    if tag == 5:
        return _dict_decode(_unlzma1(body, 3, 0))
    if tag == 6:
        return _dict_decode(bz2.decompress(body))
    raise ValueError("Unknown tag")
